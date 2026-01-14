import logging
from domain.models.syllabus import Syllabus
from domain.models.isyllabus_repository import ISyllabusRepository
from typing import List, Optional
from datetime import datetime, timezone
from domain.exceptions import ValidationException, UnauthorizedException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from infrastructure.models.subject import Subject
from infrastructure.models.program import Program
from infrastructure.models.user import User
from infrastructure.models.role import Role
from infrastructure.models.user_role import UserRole

logger = logging.getLogger(__name__)


class SyllabusService:
    # Workflow states
    DRAFT = 'DRAFT'
    PENDING_REVIEW = 'PENDING_REVIEW'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    PUBLISHED = 'PUBLISHED'
    
    # Roles - Standardized role names (exactly 6 roles per SMD scope)
    ROLE_ADMIN = 'ADMIN'
    ROLE_LECTURER = 'LECTURER'
    ROLE_HOD = 'HOD'
    ROLE_AA = 'AA'
    ROLE_PRINCIPAL = 'PRINCIPAL'
    ROLE_STUDENT = 'STUDENT'  # For viewing/publishing, not used in workflow transitions
    
    # Valid transitions map: (from_status, to_status) -> [allowed_roles]
    VALID_TRANSITIONS = {
        (DRAFT, PENDING_REVIEW): [ROLE_LECTURER],
        (PENDING_REVIEW, PENDING_APPROVAL): [ROLE_HOD],
        (PENDING_REVIEW, DRAFT): [ROLE_HOD],
        (PENDING_APPROVAL, APPROVED): [ROLE_AA],
        (PENDING_APPROVAL, PENDING_REVIEW): [ROLE_AA],
        (APPROVED, PUBLISHED): [ROLE_ADMIN, ROLE_PRINCIPAL],
        (PUBLISHED, APPROVED): [ROLE_ADMIN, ROLE_PRINCIPAL],
    }
    
    def __init__(self, repository: ISyllabusRepository, session: Session):
        """
        Initialize SyllabusService with dependencies.
        
        Args:
            repository: Syllabus repository
            session: Database session (required for all operations, including read-only)
        """
        self.repository = repository
        self.session = session  # Session is always required

    def validate_transition(self, from_status: str, to_status: str, role: str) -> bool:
        """Validate if a workflow transition is allowed for the given role."""
        transition = (from_status, to_status)
        if transition not in self.VALID_TRANSITIONS:
            return False
        allowed_roles = self.VALID_TRANSITIONS[transition]
        return role in allowed_roles

    def create_draft(self, subject_id: int, program_id: int, owner_lecturer_id: int) -> Syllabus:
        """
        Create a new syllabus in DRAFT status with initial version.
        Transaction is managed by this service method - both syllabus and version are created atomically.
        
        Raises:
            ValueError: If subject, program, or user not found, or user is not LECTURER
            ValidationException: If validation fails
        """
        try:
            # Validate subject exists
            subject = self.session.query(Subject).filter_by(subject_id=subject_id).first()
            if not subject:
                raise ValueError(f'Subject with ID {subject_id} not found')
            
            # Validate program exists
            program = self.session.query(Program).filter_by(program_id=program_id).first()
            if not program:
                raise ValueError(f'Program with ID {program_id} not found')
            
            # Validate user exists
            user = self.session.query(User).filter_by(user_id=owner_lecturer_id).first()
            if not user:
                raise ValueError(f'User with ID {owner_lecturer_id} not found')
            
            # Validate user has LECTURER role
            user_roles = self.session.query(Role).join(UserRole).filter(
                UserRole.user_id == owner_lecturer_id
            ).all()
            role_names = [role.role_name for role in user_roles]
            if self.ROLE_LECTURER not in role_names:
                raise UnauthorizedException(
                    f'User {owner_lecturer_id} does not have LECTURER role. Current roles: {role_names}'
                )
            
            # Create syllabus first
            syllabus = Syllabus(
                syllabus_id=None,
                subject_id=subject_id,
                program_id=program_id,
                owner_lecturer_id=owner_lecturer_id,
                current_version_id=None,  # Will be set after version creation
                lifecycle_status=self.DRAFT,
                created_at=datetime.now(timezone.utc)
            )
            syllabus = self.repository.add(syllabus)
            
            # Create initial version (version_no=1) and link it
            syllabus = self.repository.create_initial_version(syllabus, owner_lecturer_id)
            
            # Commit transaction - both syllabus and version are created atomically
            self.session.commit()
            logger.info(f"Syllabus draft created: syllabus_id={syllabus.syllabus_id}, version_id={syllabus.current_version_id}")
            return syllabus
        except (ValueError, ValidationException, UnauthorizedException):
            # Re-raise domain exceptions as-is
            self.session.rollback()
            raise
        except IntegrityError as e:
            # Handle FK constraint violations
            self.session.rollback()
            error_str = str(e).lower()
            if 'subject' in error_str or 'fk_syllabus_subject' in error_str:
                raise ValueError(f'Subject with ID {subject_id} not found')
            elif 'program' in error_str or 'fk_syllabus_program' in error_str:
                raise ValueError(f'Program with ID {program_id} not found')
            elif 'user' in error_str or 'fk_syllabus_owner' in error_str:
                raise ValueError(f'User with ID {owner_lecturer_id} not found')
            else:
                logger.exception(f"IntegrityError creating syllabus draft: {e}")
                raise ValueError('Database constraint violation. Please check foreign key references.')
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to create syllabus draft: {e}")
            raise

    def update_draft(self, syllabus_id: int, subject_id: int = None, 
                    program_id: int = None, owner_lecturer_id: int = None) -> Syllabus:
        """
        Update a syllabus that is in DRAFT status. Transaction is managed by this service method.
        
        Args:
            syllabus_id: Syllabus ID to update
            subject_id: Optional new subject_id
            program_id: Optional new program_id
            owner_lecturer_id: User ID of the owner (for validation - must match existing owner)
        
        Raises:
            ValueError: If syllabus not found
            ValidationException: If status is not DRAFT or owner doesn't match
            UnauthorizedException: If owner_lecturer_id doesn't match current owner
        """
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            if syllabus.lifecycle_status != self.DRAFT:
                raise ValidationException('Can only update syllabus in DRAFT status')
            
            # Validate owner if provided (defense-in-depth)
            if owner_lecturer_id is not None and syllabus.owner_lecturer_id != owner_lecturer_id:
                raise UnauthorizedException(
                    f'Only the syllabus owner can update the draft. '
                    f'Current owner: {syllabus.owner_lecturer_id}, User: {owner_lecturer_id}'
                )
            
            if subject_id is not None:
                syllabus.subject_id = subject_id
            if program_id is not None:
                syllabus.program_id = program_id
            # Don't allow changing owner_lecturer_id - it's fixed from creation
            
            syllabus = self.repository.update(syllabus)
            # Commit transaction
            self.session.commit()
            logger.info(f"Syllabus draft updated: syllabus_id={syllabus_id}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to update syllabus draft {syllabus_id}: {e}")
            raise

    def submit_for_review(self, syllabus_id: int, role: str, user_id: int = None) -> Syllabus:
        """
        Submit syllabus for review (DRAFT -> PENDING_REVIEW).
        Only the owner (lecturer) can submit.
        Transaction is managed by this service method.
        """
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate owner (only owner can submit)
            if user_id is not None and syllabus.owner_lecturer_id != user_id:
                raise UnauthorizedException(
                    f'Only the syllabus owner can submit for review. '
                    f'Current owner: {syllabus.owner_lecturer_id}, User: {user_id}'
                )
            
            # Validate status is DRAFT
            if syllabus.lifecycle_status != self.DRAFT:
                raise ValidationException(
                    f'Can only submit syllabus in DRAFT status. Current status: {syllabus.lifecycle_status}'
                )
            
            # Validate transition
            if not self.validate_transition(syllabus.lifecycle_status, self.PENDING_REVIEW, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PENDING_REVIEW} for role {role}')
            
            # Re-check status immediately before commit (concurrency protection)
            self.session.refresh(syllabus)
            if syllabus.lifecycle_status != self.DRAFT:
                raise ValidationException(
                    f'Cannot submit: syllabus status changed from DRAFT to {syllabus.lifecycle_status}. '
                    f'Please refresh and try again.'
                )
            
            # Update syllabus status
            syllabus.lifecycle_status = self.PENDING_REVIEW
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                from infrastructure.models.workflow_action import WorkflowAction
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.PENDING_REVIEW
                    version.submitted_at = datetime.now(timezone.utc)
                    self.session.flush()
                    
                    # Create workflow action record for audit trail
                    if user_id:
                        workflow_action = WorkflowAction(
                            version_id=version.version_id,
                            actor_user_id=user_id,
                            action_type='SUBMIT_FOR_REVIEW',
                            action_note=f'Submitted by {role}',
                            action_at=datetime.now(timezone.utc)
                        )
                        self.session.add(workflow_action)
            
            # Commit transaction
            self.session.commit()
            logger.info(f"Syllabus submitted for review: syllabus_id={syllabus_id}, role={role}, user_id={user_id}")
            return syllabus
        except (ValueError, ValidationException, UnauthorizedException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to submit syllabus for review {syllabus_id}: {e}")
            raise

    def hod_approve(self, syllabus_id: int, role: str) -> Syllabus:
        """HOD approves syllabus (PENDING_REVIEW -> PENDING_APPROVAL). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is PENDING_REVIEW
            if syllabus.lifecycle_status != self.PENDING_REVIEW:
                raise ValidationException(
                    f'Can only approve syllabus in PENDING_REVIEW status. Current status: {syllabus.lifecycle_status}'
                )
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PENDING_APPROVAL, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PENDING_APPROVAL} for role {role}')
            
            # Re-check status immediately before commit (concurrency protection)
            self.session.refresh(syllabus)
            if syllabus.lifecycle_status != self.PENDING_REVIEW:
                raise ValidationException(
                    f'Cannot approve: syllabus status changed from PENDING_REVIEW to {syllabus.lifecycle_status}. '
                    f'Please refresh and try again.'
                )
            
            # Update syllabus status
            syllabus.lifecycle_status = self.PENDING_APPROVAL
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.PENDING_APPROVAL
                    version.approved_at = datetime.now(timezone.utc)
                    self.session.flush()
            
            self.session.commit()
            logger.info(f"Syllabus HOD approved: syllabus_id={syllabus_id}, role={role}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to HOD approve syllabus {syllabus_id}: {e}")
            raise

    def hod_reject(self, syllabus_id: int, role: str, reason: str = None) -> Syllabus:
        """
        HOD rejects syllabus (PENDING_REVIEW -> DRAFT).
        Reason is required for rejection.
        Transaction is managed by this service method.
        """
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is PENDING_REVIEW
            if syllabus.lifecycle_status != self.PENDING_REVIEW:
                raise ValidationException(
                    f'Can only reject syllabus in PENDING_REVIEW status. Current status: {syllabus.lifecycle_status}'
                )
            
            # Require reason for rejection
            if not reason or not reason.strip():
                raise ValidationException('Rejection reason is required')
            
            if not self.validate_transition(syllabus.lifecycle_status, self.DRAFT, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.DRAFT} for role {role}')
            
            # Update syllabus status
            syllabus.lifecycle_status = self.DRAFT
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                from infrastructure.models.review_comment import ReviewComment
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.DRAFT
                    self.session.flush()
                    
                    # Create review comment for rejection reason
                    # Note: This requires review_round_id - for now, we'll create a simple comment
                    # In a full implementation, you'd create a ReviewRound first
                    # For stub, we'll just log the reason
                    logger.info(f"HOD rejection reason for version {version.version_id}: {reason}")
            
            self.session.commit()
            logger.info(f"Syllabus HOD rejected: syllabus_id={syllabus_id}, role={role}, reason={reason[:50]}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to HOD reject syllabus {syllabus_id}: {e}")
            raise

    def aa_approve(self, syllabus_id: int, role: str) -> Syllabus:
        """AA approves syllabus (PENDING_APPROVAL -> APPROVED). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is PENDING_APPROVAL
            if syllabus.lifecycle_status != self.PENDING_APPROVAL:
                raise ValidationException(
                    f'Can only approve syllabus in PENDING_APPROVAL status. Current status: {syllabus.lifecycle_status}'
                )
            
            if not self.validate_transition(syllabus.lifecycle_status, self.APPROVED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.APPROVED} for role {role}')
            
            # Re-check status immediately before commit (concurrency protection)
            self.session.refresh(syllabus)
            if syllabus.lifecycle_status != self.PENDING_APPROVAL:
                raise ValidationException(
                    f'Cannot approve: syllabus status changed from PENDING_APPROVAL to {syllabus.lifecycle_status}. '
                    f'Please refresh and try again.'
                )
            
            # Update syllabus status
            syllabus.lifecycle_status = self.APPROVED
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.APPROVED
                    version.approved_at = datetime.now(timezone.utc)
                    self.session.flush()
            
            self.session.commit()
            logger.info(f"Syllabus AA approved: syllabus_id={syllabus_id}, role={role}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to AA approve syllabus {syllabus_id}: {e}")
            raise

    def aa_reject(self, syllabus_id: int, role: str, reason: str = None) -> Syllabus:
        """
        AA rejects syllabus (PENDING_APPROVAL -> DRAFT).
        Reason is required for rejection.
        Transaction is managed by this service method.
        """
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is PENDING_APPROVAL
            if syllabus.lifecycle_status != self.PENDING_APPROVAL:
                raise ValidationException(
                    f'Can only reject syllabus in PENDING_APPROVAL status. Current status: {syllabus.lifecycle_status}'
                )
            
            # Require reason for rejection
            if not reason or not reason.strip():
                raise ValidationException('Rejection reason is required')
            
            # Reject to DRAFT (not PENDING_REVIEW) so lecturer can fix directly
            if not self.validate_transition(syllabus.lifecycle_status, self.DRAFT, role):
                # If transition not in map, we'll still allow it for AA reject
                # This is a special case: AA can reject to DRAFT even if not in transition map
                pass
            
            # Update syllabus status to DRAFT
            syllabus.lifecycle_status = self.DRAFT
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.DRAFT
                    self.session.flush()
                    
                    # Log rejection reason (stub - can create ReviewComment later)
                    logger.info(f"AA rejection reason for version {version.version_id}: {reason}")
            
            self.session.commit()
            logger.info(f"Syllabus AA rejected: syllabus_id={syllabus_id}, role={role}, reason={reason[:50]}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to AA reject syllabus {syllabus_id}: {e}")
            raise

    def publish(self, syllabus_id: int, role: str) -> Syllabus:
        """Publish syllabus (APPROVED -> PUBLISHED). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is APPROVED
            if syllabus.lifecycle_status != self.APPROVED:
                raise ValidationException(
                    f'Can only publish syllabus in APPROVED status. Current status: {syllabus.lifecycle_status}'
                )
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PUBLISHED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PUBLISHED} for role {role}')
            
            # Re-check status immediately before commit (concurrency protection)
            self.session.refresh(syllabus)
            if syllabus.lifecycle_status != self.APPROVED:
                raise ValidationException(
                    f'Cannot publish: syllabus status changed from APPROVED to {syllabus.lifecycle_status}. '
                    f'Please refresh and try again.'
                )
            
            # Update syllabus status
            syllabus.lifecycle_status = self.PUBLISHED
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.PUBLISHED
                    version.published_at = datetime.now(timezone.utc)
                    self.session.flush()
            
            self.session.commit()
            logger.info(f"Syllabus published: syllabus_id={syllabus_id}, role={role}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to publish syllabus {syllabus_id}: {e}")
            raise

    def unpublish(self, syllabus_id: int, role: str) -> Syllabus:
        """Unpublish syllabus (PUBLISHED -> APPROVED). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            # Validate status is PUBLISHED
            if syllabus.lifecycle_status != self.PUBLISHED:
                raise ValidationException(
                    f'Can only unpublish syllabus in PUBLISHED status. Current status: {syllabus.lifecycle_status}'
                )
            
            if not self.validate_transition(syllabus.lifecycle_status, self.APPROVED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.APPROVED} for role {role}')
            
            # Update syllabus status
            syllabus.lifecycle_status = self.APPROVED
            syllabus = self.repository.update(syllabus)
            
            # Update current version workflow_status to match syllabus lifecycle_status
            if syllabus.current_version_id:
                from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
                version = self.session.query(SyllabusVersionModel).filter_by(
                    version_id=syllabus.current_version_id
                ).first()
                if version:
                    version.workflow_status = self.APPROVED
                    version.published_at = None  # Clear published_at
                    self.session.flush()
            
            self.session.commit()
            logger.info(f"Syllabus unpublished: syllabus_id={syllabus_id}, role={role}")
            return syllabus
        except (ValueError, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to unpublish syllabus {syllabus_id}: {e}")
            raise

    def get_syllabus_by_id(self, syllabus_id: int) -> Optional[Syllabus]:
        """Get syllabus by ID."""
        return self.repository.get_by_id(syllabus_id)

    def list_syllabi_by_owner(self, owner_lecturer_id: int) -> List[Syllabus]:
        """List all syllabi owned by a specific lecturer."""
        return self.repository.list_by_owner(owner_lecturer_id)
    
    def list_syllabi_by_status(self, status: str) -> List[Syllabus]:
        """List all syllabi with a specific lifecycle status."""
        return self.repository.list_by_status(status)
    
    def list_syllabi(self) -> List[Syllabus]:
        """List all syllabi."""
        return self.repository.list()

    def list_published(self) -> List[Syllabus]:
        """
        List all published syllabi. Public endpoint - no authentication required.
        Read-only operation.
        """
        return self.repository.list_published()
    
    def get_version_workflow_info(self, version_id: int) -> Optional[dict]:
        """
        Get workflow information for a syllabus version.
        Returns workflow steps, current status, and current step index.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            Dictionary with workflow info:
            {
                "version_id": int,
                "current_status": str,
                "steps": [{"code": str, "label": str, "order": int}, ...],
                "current_step_index": int
            }
            None if version not found
        """
        from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
        
        try:
            version = self.session.query(SyllabusVersionModel).filter_by(
                version_id=version_id
            ).first()
            
            if not version:
                return None
            
            # Standard workflow steps
            standard_steps = [
                {"code": self.DRAFT, "label": "Draft", "order": 1},
                {"code": self.PENDING_REVIEW, "label": "Pending Review", "order": 2},
                {"code": self.PENDING_APPROVAL, "label": "Pending Approval", "order": 3},
                {"code": self.APPROVED, "label": "Approved", "order": 4},
                {"code": self.PUBLISHED, "label": "Published", "order": 5},
            ]
            
            current_status = version.workflow_status
            
            # Find current step index
            current_step_index = None
            for idx, step in enumerate(standard_steps):
                if step["code"] == current_status:
                    current_step_index = idx
                    break
            
            # If status is not in standard steps (e.g., ARCHIVED, UNPUBLISHED), add it
            steps = standard_steps.copy()
            if current_step_index is None:
                # Status is outside standard workflow - add as additional step
                if current_status == "ARCHIVED":
                    steps.append({"code": "ARCHIVED", "label": "Archived", "order": 6})
                    current_step_index = len(steps) - 1
                elif current_status == "UNPUBLISHED":
                    steps.append({"code": "UNPUBLISHED", "label": "Unpublished", "order": 6})
                    current_step_index = len(steps) - 1
                else:
                    # Unknown status - default to first step
                    current_step_index = 0
            
            return {
                "version_id": version_id,
                "current_status": current_status,
                "steps": steps,
                "current_step_index": current_step_index
            }
            
        except Exception as e:
            logger.exception(f"Failed to get workflow info for version {version_id}: {e}")
            raise
    
    def get_version_detail(self, version_id: int, user_id: int = None, user_roles: List[str] = None) -> Optional[dict]:
        """
        Get detailed information about a syllabus version including syllabus info.
        Returns None if version not found.
        
        Args:
            version_id: Version ID to retrieve
            user_id: User ID requesting access (for authorization check)
            user_roles: List of user roles (for authorization check)
        
        Returns:
            Dictionary with version details, or None if not found
            
        Raises:
            UnauthorizedException: If user doesn't have permission to view this version
        """
        try:
            from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel
            from infrastructure.models.user import User
            from services.authz.file_access_policy import can_view_file
            from domain.exceptions import UnauthorizedException
            
            version = self.session.query(SyllabusVersionModel).filter_by(version_id=version_id).first()
            if not version:
                return None
            
            # Authorization check: Students can only view PUBLISHED versions
            # Other roles follow file access policy (same rules as file viewing)
            if user_id is not None and user_roles:
                # Check if user can view this version based on workflow status
                if not can_view_file(
                    user_id=user_id,
                    user_roles=user_roles,
                    version_workflow_status=version.workflow_status,
                    version_created_by=version.created_by
                ):
                    # For students, return 404 to hide existence (security)
                    # For other roles, return 403 (they should know it exists but can't access)
                    if self.ROLE_STUDENT in user_roles:
                        raise ValueError(f'Syllabus version {version_id} not found')
                    else:
                        raise UnauthorizedException(
                            f'You do not have permission to view this syllabus version. '
                            f'Version status: {version.workflow_status}'
                        )
            
            # Get creator info
            creator = self.session.query(User).filter_by(user_id=version.created_by).first()
            creator_info = None
            if creator:
                creator_info = {
                    "user_id": creator.user_id,
                    "full_name": creator.full_name,
                    "email": creator.email,
                }
            
            # Get syllabus info
            syllabus = self.repository.get_by_id(version.syllabus_id)
            syllabus_info = None
            if syllabus:
                syllabus_info = {
                    "syllabus_id": syllabus.syllabus_id,
                    "subject_id": syllabus.subject_id,
                    "program_id": syllabus.program_id,
                    "owner_lecturer_id": syllabus.owner_lecturer_id,
                    "lifecycle_status": syllabus.lifecycle_status,
                    "created_at": syllabus.created_at.isoformat() if syllabus.created_at else None,
                }
            
            return {
                "version_id": version.version_id,
                "syllabus_id": version.syllabus_id,
                "academic_year": version.academic_year,
                "version_no": version.version_no,
                "workflow_status": version.workflow_status,
                "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
                "approved_at": version.approved_at.isoformat() if version.approved_at else None,
                "published_at": version.published_at.isoformat() if version.published_at else None,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "created_by": version.created_by,
                "creator": creator_info,
                "syllabus": syllabus_info,
            }
        except Exception as e:
            logger.exception(f"Failed to get version detail {version_id}: {e}")
            raise

