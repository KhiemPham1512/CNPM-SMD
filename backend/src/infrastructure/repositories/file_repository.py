"""
File Asset Repository

Handles database operations for file assets.
Converts between domain models and SQLAlchemy models.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from domain.models.ifile_repository import IFileRepository
from domain.models.file_asset import FileAsset
from infrastructure.models.file_asset import FileAsset as FileAssetModel
from infrastructure.models.syllabus_version import SyllabusVersion as SyllabusVersionModel

logger = logging.getLogger(__name__)


class FileRepository(IFileRepository):
    """Repository for file asset operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def create(self, file_asset: FileAsset) -> FileAsset:
        """
        Create a new file asset record.
        Does NOT commit - transaction managed by service layer.
        """
        try:
            file_model = FileAssetModel(
                syllabus_version_id=file_asset.syllabus_version_id,
                original_filename=file_asset.original_filename,
                display_name=file_asset.display_name,
                bucket=file_asset.bucket,
                object_path=file_asset.object_path,
                mime_type=file_asset.mime_type,
                size_bytes=file_asset.size_bytes,
                uploaded_by=file_asset.uploaded_by,
                created_at=file_asset.created_at
            )
            self.session.add(file_model)
            self.session.flush()  # Flush to get ID, but don't commit
            self.session.refresh(file_model)
            return self._to_domain(file_model)
        except Exception as e:
            logger.exception(f"Failed to create file asset: {e}")
            raise  # Re-raise original exception
    
    def get_by_id(self, file_id: int) -> Optional[FileAsset]:
        """
        Get file asset by ID.
        Read-only operation.
        """
        try:
            file_model = self.session.query(FileAssetModel).filter_by(file_id=file_id).first()
            if file_model:
                return self._to_domain(file_model)
            return None
        except Exception as e:
            logger.exception(f"Failed to get file asset by id {file_id}: {e}")
            raise  # Re-raise original exception
    
    def list_by_version(self, version_id: int) -> List[FileAsset]:
        """
        List all file assets for a syllabus version.
        Read-only operation.
        """
        try:
            file_models = self.session.query(FileAssetModel).filter_by(
                syllabus_version_id=version_id
            ).all()
            return [self._to_domain(file_model) for file_model in file_models]
        except Exception as e:
            logger.exception(f"Failed to list file assets for version {version_id}: {e}")
            raise  # Re-raise original exception
    
    def delete(self, file_id: int) -> None:
        """
        Delete file asset by ID.
        Does NOT commit - transaction managed by service layer.
        """
        try:
            file_model = self.session.query(FileAssetModel).filter_by(file_id=file_id).first()
            if file_model:
                self.session.delete(file_model)
                self.session.flush()  # Flush deletion, but don't commit
            else:
                raise ValueError(f'File asset {file_id} not found')
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.exception(f"Failed to delete file asset {file_id}: {e}")
            raise  # Re-raise original exception
    
    def verify_version_exists(self, version_id: int) -> bool:
        """
        Verify that a syllabus version exists.
        Read-only operation.
        """
        try:
            version = self.session.query(SyllabusVersionModel).filter_by(
                version_id=version_id
            ).first()
            return version is not None
        except Exception as e:
            logger.exception(f"Failed to verify version {version_id}: {e}")
            raise  # Re-raise original exception
    
    def get_version_syllabus_id(self, version_id: int) -> Optional[int]:
        """
        Get syllabus_id for a given version_id.
        Read-only operation.
        """
        try:
            version = self.session.query(SyllabusVersionModel).filter_by(
                version_id=version_id
            ).first()
            if version:
                return version.syllabus_id
            return None
        except Exception as e:
            logger.exception(f"Failed to get syllabus_id for version {version_id}: {e}")
            raise  # Re-raise original exception
    
    def get_version_workflow_status(self, version_id: int) -> Optional[str]:
        """
        Get workflow_status for a given version_id.
        Read-only operation.
        Used for authorization checks (e.g., deny student unless published).
        """
        try:
            version = self.session.query(SyllabusVersionModel).filter_by(
                version_id=version_id
            ).first()
            if version:
                return version.workflow_status
            return None
        except Exception as e:
            logger.exception(f"Failed to get workflow_status for version {version_id}: {e}")
            raise  # Re-raise original exception
    
    def get_version_info(self, version_id: int) -> Optional[tuple]:
        """
        Get version info (workflow_status, created_by) for authorization checks.
        Read-only operation.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            Tuple of (workflow_status, created_by) if version exists, None otherwise
        """
        try:
            version = self.session.query(SyllabusVersionModel).filter_by(
                version_id=version_id
            ).first()
            if version:
                return (version.workflow_status, version.created_by)
            return None
        except Exception as e:
            logger.exception(f"Failed to get version info for version {version_id}: {e}")
            raise  # Re-raise original exception
    
    def update_display_name(self, file_id: int, display_name: str) -> FileAsset:
        """
        Update display_name of a file asset.
        Does NOT commit - transaction managed by service layer.
        """
        try:
            file_model = self.session.query(FileAssetModel).filter_by(file_id=file_id).first()
            if not file_model:
                raise ValueError(f'File asset {file_id} not found')
            
            file_model.display_name = display_name
            self.session.flush()
            self.session.refresh(file_model)
            return self._to_domain(file_model)
        except ValueError:
            raise
        except Exception as e:
            logger.exception(f"Failed to update display_name for file {file_id}: {e}")
            raise
    
    def update_file_content(
        self,
        file_id: int,
        original_filename: str,
        object_path: str,
        mime_type: str,
        size_bytes: int,
        uploaded_by: int
    ) -> FileAsset:
        """
        Update file content metadata (for replace operation).
        Does NOT commit - transaction managed by service layer.
        """
        try:
            file_model = self.session.query(FileAssetModel).filter_by(file_id=file_id).first()
            if not file_model:
                raise ValueError(f'File asset {file_id} not found')
            
            file_model.original_filename = original_filename
            file_model.object_path = object_path
            file_model.mime_type = mime_type
            file_model.size_bytes = size_bytes
            file_model.uploaded_by = uploaded_by
            
            self.session.flush()
            self.session.refresh(file_model)
            return self._to_domain(file_model)
        except ValueError:
            raise
        except Exception as e:
            logger.exception(f"Failed to update file content for file {file_id}: {e}")
            raise
    
    def _to_domain(self, file_model: FileAssetModel) -> FileAsset:
        """
        Convert SQLAlchemy model to domain model.
        
        Args:
            file_model: SQLAlchemy FileAsset model
            
        Returns:
            FileAsset domain model
        """
        return FileAsset(
            file_id=file_model.file_id,
            syllabus_version_id=file_model.syllabus_version_id,
            original_filename=file_model.original_filename,
            display_name=file_model.display_name,
            bucket=file_model.bucket,
            object_path=file_model.object_path,
            mime_type=file_model.mime_type,
            size_bytes=file_model.size_bytes,
            uploaded_by=file_model.uploaded_by,
            created_at=file_model.created_at
        )
