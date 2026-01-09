import logging
from domain.models.syllabus import Syllabus
from domain.models.isyllabus_repository import ISyllabusRepository
from typing import List, Optional
from datetime import datetime, timezone
from domain.exceptions import ValidationException, UnauthorizedException
from sqlalchemy.orm import Session

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
        """
        try:
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
            logger.info(f"Syllabus draft created: syllabus_id={syllabus.syllabus_id}")
            return syllabus
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to create syllabus draft: {e}")
            raise

    def update_draft(self, syllabus_id: int, subject_id: int = None, 
                    program_id: int = None, owner_lecturer_id: int = None) -> Syllabus:
        """Update a syllabus that is in DRAFT status. Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            if syllabus.lifecycle_status != self.DRAFT:
                raise ValidationException('Can only update syllabus in DRAFT status')
            
            if subject_id is not None:
                syllabus.subject_id = subject_id
            if program_id is not None:
                syllabus.program_id = program_id
            if owner_lecturer_id is not None:
                syllabus.owner_lecturer_id = owner_lecturer_id
            
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

    def submit_for_review(self, syllabus_id: int, role: str) -> Syllabus:
        """Submit syllabus for review (DRAFT -> PENDING_REVIEW). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PENDING_REVIEW, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PENDING_REVIEW} for role {role}')
            
            syllabus.lifecycle_status = self.PENDING_REVIEW
            syllabus = self.repository.update(syllabus)
            # Commit transaction
            self.session.commit()
            logger.info(f"Syllabus submitted for review: syllabus_id={syllabus_id}, role={role}")
            return syllabus
        except (ValueError, ValidationException):
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
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PENDING_APPROVAL, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PENDING_APPROVAL} for role {role}')
            
            syllabus.lifecycle_status = self.PENDING_APPROVAL
            syllabus = self.repository.update(syllabus)
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

    def hod_reject(self, syllabus_id: int, role: str) -> Syllabus:
        """HOD rejects syllabus (PENDING_REVIEW -> DRAFT). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            if not self.validate_transition(syllabus.lifecycle_status, self.DRAFT, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.DRAFT} for role {role}')
            
            syllabus.lifecycle_status = self.DRAFT
            syllabus = self.repository.update(syllabus)
            self.session.commit()
            logger.info(f"Syllabus HOD rejected: syllabus_id={syllabus_id}, role={role}")
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
            
            if not self.validate_transition(syllabus.lifecycle_status, self.APPROVED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.APPROVED} for role {role}')
            
            syllabus.lifecycle_status = self.APPROVED
            syllabus = self.repository.update(syllabus)
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

    def aa_reject(self, syllabus_id: int, role: str) -> Syllabus:
        """AA rejects syllabus (PENDING_APPROVAL -> PENDING_REVIEW). Transaction is managed by this service method."""
        if not self.session:
            raise ValueError("Database session is required for transaction management")
        
        try:
            syllabus = self.repository.get_by_id(syllabus_id)
            if not syllabus:
                raise ValueError('Syllabus not found')
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PENDING_REVIEW, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PENDING_REVIEW} for role {role}')
            
            syllabus.lifecycle_status = self.PENDING_REVIEW
            syllabus = self.repository.update(syllabus)
            self.session.commit()
            logger.info(f"Syllabus AA rejected: syllabus_id={syllabus_id}, role={role}")
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
            
            if not self.validate_transition(syllabus.lifecycle_status, self.PUBLISHED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.PUBLISHED} for role {role}')
            
            syllabus.lifecycle_status = self.PUBLISHED
            syllabus = self.repository.update(syllabus)
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
            
            if not self.validate_transition(syllabus.lifecycle_status, self.APPROVED, role):
                raise ValidationException(f'Invalid transition from {syllabus.lifecycle_status} to {self.APPROVED} for role {role}')
            
            syllabus.lifecycle_status = self.APPROVED
            syllabus = self.repository.update(syllabus)
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

    def list_syllabi(self) -> List[Syllabus]:
        """List all syllabi."""
        return self.repository.list()

    def list_published(self) -> List[Syllabus]:
        """
        List all published syllabi. Public endpoint - no authentication required.
        Read-only operation.
        """
        return self.repository.list_published()

