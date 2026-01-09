import logging
from datetime import datetime, timezone
from domain.models.isyllabus_repository import ISyllabusRepository
from domain.models.syllabus import Syllabus
from typing import List, Optional
from sqlalchemy.orm import Session
from infrastructure.models.syllabus import Syllabus as SyllabusModel
from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel

logger = logging.getLogger(__name__)


class SyllabusRepository(ISyllabusRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, syllabus: Syllabus) -> Syllabus:
        """Add syllabus to session. Does NOT commit - transaction managed by service layer."""
        try:
            syllabus_model = SyllabusModel(
                subject_id=syllabus.subject_id,
                program_id=syllabus.program_id,
                owner_lecturer_id=syllabus.owner_lecturer_id,
                current_version_id=syllabus.current_version_id,
                lifecycle_status=syllabus.lifecycle_status,
                created_at=syllabus.created_at
            )
            self.session.add(syllabus_model)
            self.session.flush()  # Flush to get ID, but don't commit
            self.session.refresh(syllabus_model)
            return self._to_domain(syllabus_model)
        except Exception as e:
            logger.exception(f"Failed to add syllabus to session: {e}")
            raise  # Re-raise original exception to preserve stack trace

    def get_by_id(self, syllabus_id: int) -> Optional[Syllabus]:
        """Get syllabus by ID. Read-only operation."""
        try:
            syllabus_model = self.session.query(SyllabusModel).filter_by(syllabus_id=syllabus_id).first()
            if syllabus_model:
                return self._to_domain(syllabus_model)
            return None
        except Exception as e:
            logger.exception(f"Failed to get syllabus by id {syllabus_id}: {e}")
            raise  # Re-raise original exception

    def list(self) -> List[Syllabus]:
        """List all syllabi. Read-only operation."""
        try:
            syllabus_models = self.session.query(SyllabusModel).all()
            return [self._to_domain(syllabus_model) for syllabus_model in syllabus_models]
        except Exception as e:
            logger.exception(f"Failed to list syllabi: {e}")
            raise  # Re-raise original exception

    def update(self, syllabus: Syllabus) -> Syllabus:
        """Update syllabus in session. Does NOT commit - transaction managed by service layer."""
        try:
            syllabus_model = self.session.query(SyllabusModel).filter_by(syllabus_id=syllabus.syllabus_id).first()
            if not syllabus_model:
                raise ValueError('Syllabus not found')
            
            syllabus_model.subject_id = syllabus.subject_id
            syllabus_model.program_id = syllabus.program_id
            syllabus_model.owner_lecturer_id = syllabus.owner_lecturer_id
            syllabus_model.current_version_id = syllabus.current_version_id
            syllabus_model.lifecycle_status = syllabus.lifecycle_status
            
            self.session.flush()  # Flush changes, but don't commit
            self.session.refresh(syllabus_model)
            return self._to_domain(syllabus_model)
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.exception(f"Failed to update syllabus {syllabus.syllabus_id}: {e}")
            raise  # Re-raise original exception

    def delete(self, syllabus_id: int) -> None:
        """Delete syllabus from session. Does NOT commit - transaction managed by service layer."""
        try:
            syllabus_model = self.session.query(SyllabusModel).filter_by(syllabus_id=syllabus_id).first()
            if syllabus_model:
                self.session.delete(syllabus_model)
                self.session.flush()  # Flush deletion, but don't commit
            else:
                raise ValueError('Syllabus not found')
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.exception(f"Failed to delete syllabus {syllabus_id}: {e}")
            raise  # Re-raise original exception

    def create_initial_version(self, syllabus: Syllabus, created_by_user_id: int) -> Syllabus:
        """Create initial SyllabusVersion (version_no=1) and link it to syllabus.
        Does NOT commit - transaction managed by service layer."""
        try:
            # Get current academic year (simplified - can be enhanced later)
            current_year = datetime.now(timezone.utc).year
            academic_year = f"{current_year}-{current_year + 1}"
            
            # Create version with workflow_status matching syllabus lifecycle_status
            version_model = SyllabusVersionModel(
                syllabus_id=syllabus.syllabus_id,
                academic_year=academic_year,
                version_no=1,
                workflow_status=syllabus.lifecycle_status,  # Match syllabus status
                submitted_at=None,
                approved_at=None,
                published_at=None,
                created_by=created_by_user_id,
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(version_model)
            self.session.flush()  # Get version_id, but don't commit
            
            # Update syllabus with current_version_id
            syllabus.current_version_id = version_model.version_id
            syllabus_model = self.session.query(SyllabusModel).filter_by(syllabus_id=syllabus.syllabus_id).first()
            syllabus_model.current_version_id = version_model.version_id
            
            self.session.flush()  # Flush changes, but don't commit
            self.session.refresh(syllabus_model)
            return self._to_domain(syllabus_model)
        except Exception as e:
            logger.exception(f"Failed to create initial version for syllabus {syllabus.syllabus_id}: {e}")
            raise  # Re-raise original exception

    def list_published(self) -> List[Syllabus]:
        """List all published syllabi. Read-only operation."""
        try:
            syllabus_models = self.session.query(SyllabusModel).filter_by(
                lifecycle_status='PUBLISHED'
            ).all()
            return [self._to_domain(syllabus_model) for syllabus_model in syllabus_models]
        except Exception as e:
            logger.exception(f"Failed to list published syllabi: {e}")
            raise  # Re-raise original exception

    def _to_domain(self, syllabus_model: SyllabusModel) -> Syllabus:
        return Syllabus(
            syllabus_id=syllabus_model.syllabus_id,
            subject_id=syllabus_model.subject_id,
            program_id=syllabus_model.program_id,
            owner_lecturer_id=syllabus_model.owner_lecturer_id,
            current_version_id=syllabus_model.current_version_id,
            lifecycle_status=syllabus_model.lifecycle_status,
            created_at=syllabus_model.created_at
        )

