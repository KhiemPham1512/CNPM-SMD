"""
File Service

Application service for file operations.
Handles business logic, transaction boundaries, and coordinates between
repository and Supabase storage service.
"""
import logging
from typing import Optional, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from domain.models.ifile_repository import IFileRepository
from domain.models.file_asset import FileAsset
from domain.exceptions import ValidationException, UnauthorizedException
from domain.constants import ROLE_LECTURER, ROLE_STUDENT
from infrastructure.services.supabase_storage import SupabaseStorageService
from services.authz.file_access_policy import can_view_file
from services.authz.file_mutation_policy import can_edit_file

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for file operations.
    Handles transaction boundaries and coordinates between storage and database.
    """
    
    def __init__(
        self,
        repository: IFileRepository,
        storage_service: SupabaseStorageService,
        session: Session
    ):
        """
        Initialize FileService with dependencies.
        
        Args:
            repository: File repository
            storage_service: Supabase storage service
            session: Database session (required for transaction management)
        """
        self.repository = repository
        self.storage_service = storage_service
        self.session = session
    
    def upload_file(
        self,
        version_id: int,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        size_bytes: int,
        user_id: int,
        user_roles: List[str] = None,
        display_name: str = None
    ) -> FileAsset:
        """
        Upload a file to Supabase Storage and save metadata to database.
        Handles compensating delete if database operation fails.
        
        Defense-in-depth: Only LECTURER role can upload files.
        This check is in addition to controller-level @role_required decorator.
        
        Transaction is managed by this service method.
        
        Args:
            version_id: Syllabus version ID
            file_bytes: File content as bytes
            filename: Original filename
            mime_type: MIME type of the file
            size_bytes: File size in bytes
            user_id: User ID who uploaded the file
            user_roles: List of user roles (for defense-in-depth authorization check)
            
        Returns:
            FileAsset domain model with file_id populated
            
        Raises:
            ValueError: If version not found or validation fails
            ValidationException: If business rules are violated
            UnauthorizedException: If user does not have LECTURER role
            Exception: If upload or database operation fails
        """
        # Defense-in-depth: Check role authorization
        # Only LECTURER can upload syllabus attachments
        if user_roles is None:
            # If roles not provided, we cannot verify - this is a security risk
            # In production, always provide user_roles from controller
            logger.warning(f"upload_file called without user_roles for user_id={user_id}. "
                         "This should not happen if called from controller with @role_required.")
        elif ROLE_LECTURER not in user_roles:
            logger.warning(f"Unauthorized upload attempt by user_id={user_id} with roles={user_roles}")
            raise UnauthorizedException(
                "Only users with LECTURER role can upload syllabus attachments"
            )
        
        # Verify version exists
        if not self.repository.verify_version_exists(version_id):
            raise ValueError(f'Syllabus version {version_id} not found')
        
        # Get syllabus_id for path organization
        syllabus_id = self.repository.get_version_syllabus_id(version_id)
        if syllabus_id is None:
            raise ValueError(f'Could not determine syllabus_id for version {version_id}')
        
        # Upload to Supabase Storage first
        object_path = None
        try:
            object_path, actual_size = self.storage_service.upload_file(
                file_data=file_bytes,
                syllabus_id=syllabus_id,
                version_id=version_id,
                original_filename=filename,
                mime_type=mime_type
            )
            # Use actual size from storage service (may differ from provided size_bytes)
            size_bytes = actual_size
        except Exception as upload_error:
            # Upload failed - no cleanup needed
            logger.error(f"Supabase upload failed: {upload_error}", exc_info=True)
            raise Exception("File upload to storage failed") from upload_error
        
        # Save metadata to database
        # If this fails, we need to cleanup the uploaded file in Supabase
        try:
            # Use provided display_name or default to filename
            if display_name is None:
                display_name = filename
            
            file_asset = FileAsset(
                file_id=None,
                syllabus_version_id=version_id,
                original_filename=filename,
                display_name=display_name,
                bucket=self.storage_service.bucket,
                object_path=object_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
                uploaded_by=user_id,
                created_at=datetime.now(timezone.utc)
            )
            
            file_asset = self.repository.create(file_asset)
            self.session.commit()
            
            logger.info(f"File uploaded successfully: file_id={file_asset.file_id}, object_path={object_path}")
            return file_asset
            
        except Exception as db_error:
            # DB operation failed - cleanup uploaded file in Supabase (best-effort with retry)
            self.session.rollback()
            logger.error(f"Database operation failed after Supabase upload: {db_error}", exc_info=True)
            
            # Attempt to delete uploaded file from Supabase with retry
            if object_path:
                cleanup_success = False
                max_retries = 3
                retry_delay = 0.5  # seconds
                
                for attempt in range(1, max_retries + 1):
                    try:
                        import time
                        if attempt > 1:
                            time.sleep(retry_delay * attempt)  # Exponential backoff
                        
                        self.storage_service.delete_object(object_path)
                        logger.info(f"Cleaned up orphaned file from Supabase: {object_path} (attempt {attempt})")
                        cleanup_success = True
                        break
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Cleanup attempt {attempt}/{max_retries} failed for {object_path}: {cleanup_error}"
                        )
                        if attempt == max_retries:
                            # Final attempt failed - log as orphaned file
                            logger.error(
                                f"ORPHANED FILE: Failed to cleanup {object_path} after {max_retries} attempts. "
                                f"Manual cleanup required. Error: {cleanup_error}",
                                exc_info=True
                            )
            
            # Raise domain exception instead of generic Exception
            from domain.exceptions import ValidationException
            raise ValidationException("File upload failed: database error. Please try again.") from db_error
    
    def get_signed_url(
        self,
        file_id: int,
        user_id: int,
        expires_in: int = 3600,
        user_roles: List[str] = None
    ) -> Tuple[str, int, str]:
        """
        Get a signed URL for downloading a file from Supabase Storage.
        
        Authorization: Students can only access files for PUBLISHED syllabus versions.
        Other roles (LECTURER, HOD, AA, PRINCIPAL, ADMIN) can access files for any version
        they have permission to view (based on syllabus ownership/workflow state).
        
        TODO: Implement full authorization check based on:
        - Lecturer (owner of syllabus) can view
        - HOD/AA/Principal can view if syllabus is in their review/approval workflow
        - Student/Public can only view if syllabus is PUBLISHED
        
        Args:
            file_id: File asset ID
            user_id: User ID requesting the URL
            expires_in: URL expiration time in seconds (default: 3600)
            user_roles: List of user roles (for authorization check)
            
        Returns:
            Tuple of (signed_url, expires_in, object_path)
            
        Raises:
            ValueError: If file not found
            UnauthorizedException: If user does not have permission to access file
            Exception: If signed URL generation fails
        """
        # Get file metadata from database
        file_asset = self.repository.get_by_id(file_id)
        if not file_asset:
            raise ValueError(f'File {file_id} not found')
        
        # Authorization check using policy
        version_info = self.repository.get_version_info(file_asset.syllabus_version_id)
        if not version_info:
            raise ValueError(f'Syllabus version {file_asset.syllabus_version_id} not found')
        
        version_status, version_created_by = version_info
        
        if not can_view_file(
            user_id=user_id,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            logger.warning(
                f"User user_id={user_id} with roles={user_roles} attempted to access "
                f"file_id={file_id} for version_id={file_asset.syllabus_version_id} "
                f"(status={version_status}, created_by={version_created_by})"
            )
            # Return 404 to avoid information leak (file exists but user cannot access)
            raise ValueError(f'File {file_id} not found')
        
        # Validate expires_in (between 1 second and 7 days)
        if expires_in < 1 or expires_in > 604800:
            raise ValidationException('expires_in must be between 1 and 604800 seconds (7 days)')
        
        # Generate signed URL from Supabase
        try:
            signed_url = self.storage_service.get_signed_url(
                object_path=file_asset.object_path,
                expires_in=expires_in
            )
            
            logger.info(f"Generated signed URL for file_id={file_id}, expires_in={expires_in}s")
            return signed_url, expires_in, file_asset.object_path
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for file_id={file_id}: {e}", exc_info=True)
            raise Exception("Failed to generate signed URL") from e
    
    def get_file_metadata(self, file_id: int, user_id: int = None, user_roles: List[str] = None) -> Optional[FileAsset]:
        """
        Get file metadata by ID.
        Read-only operation.
        
        Authorization: Students can only access files for PUBLISHED syllabus versions.
        Other roles can access files for any version they have permission to view.
        
        TODO: Implement full authorization check based on syllabus ownership/workflow state.
        
        Args:
            file_id: File asset ID
            user_id: User ID requesting metadata (for authorization check)
            user_roles: List of user roles (for authorization check)
            
        Returns:
            FileAsset if found, None otherwise
            
        Raises:
            UnauthorizedException: If user does not have permission to access file
        """
        file_asset = self.repository.get_by_id(file_id)
        if not file_asset:
            return None
        
        # Authorization check using policy
        version_info = self.repository.get_version_info(file_asset.syllabus_version_id)
        if not version_info:
            # Version not found - return None (file may be orphaned)
            return None
        
        version_status, version_created_by = version_info
        
        if not can_view_file(
            user_id=user_id or 0,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            logger.warning(
                f"User user_id={user_id} with roles={user_roles} attempted to access "
                f"file_id={file_id} for version_id={file_asset.syllabus_version_id} "
                f"(status={version_status}, created_by={version_created_by})"
            )
            # Return 404 to avoid information leak
            return None
        
        return file_asset
    
    def list_files_by_version(self, version_id: int, user_id: int = None, user_roles: List[str] = None) -> List[FileAsset]:
        """
        List all files for a syllabus version.
        Read-only operation.
        
        Authorization: Students can only access files for PUBLISHED syllabus versions.
        Other roles can access files for any version they have permission to view.
        
        TODO: Implement full authorization check based on syllabus ownership/workflow state.
        
        Args:
            version_id: Syllabus version ID
            user_id: User ID requesting list (for authorization check)
            user_roles: List of user roles (for authorization check)
            
        Returns:
            List of FileAsset objects
            
        Raises:
            ValueError: If version not found
            UnauthorizedException: If user does not have permission to access files
        """
        # Verify version exists and get version info
        version_info = self.repository.get_version_info(version_id)
        if not version_info:
            raise ValueError(f'Syllabus version {version_id} not found')
        
        version_status, version_created_by = version_info
        
        # Authorization check using policy
        if not can_view_file(
            user_id=user_id or 0,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            logger.warning(
                f"User user_id={user_id} with roles={user_roles} attempted to list files "
                f"for version_id={version_id} (status={version_status}, created_by={version_created_by})"
            )
            # Return 404 to avoid information leak
            raise ValueError(f'Syllabus version {version_id} not found')
        
        return self.repository.list_by_version(version_id)
    
    def rename_file(
        self,
        file_id: int,
        display_name: str,
        user_id: int,
        user_roles: List[str] = None
    ) -> FileAsset:
        """
        Rename display_name of a file.
        
        Authorization: Only LECTURER owner when version status is DRAFT.
        
        Args:
            file_id: File asset ID
            display_name: New display name
            user_id: User ID requesting rename
            user_roles: List of user roles
            
        Returns:
            Updated FileAsset
            
        Raises:
            ValueError: If file not found or validation fails
            UnauthorizedException: If user cannot edit file
            ValidationException: If version is not DRAFT
        """
        # Get file asset
        file_asset = self.repository.get_by_id(file_id)
        if not file_asset:
            raise ValueError(f'File {file_id} not found')
        
        # Get version info for authorization
        version_info = self.repository.get_version_info(file_asset.syllabus_version_id)
        if not version_info:
            raise ValueError(f'Syllabus version {file_asset.syllabus_version_id} not found')
        
        version_status, version_created_by = version_info
        
        # Authorization check
        if not can_edit_file(
            user_id=user_id,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            if version_status != WORKFLOW_DRAFT:
                raise ValidationException(
                    f'Cannot rename file. Syllabus version is {version_status}, not DRAFT'
                )
            raise UnauthorizedException(
                'Only the syllabus owner (LECTURER) can rename files in DRAFT status'
            )
        
        # Update display_name
        try:
            file_asset = self.repository.update_display_name(file_id, display_name)
            self.session.commit()
            logger.info(f"File {file_id} display_name updated to: {display_name}")
            return file_asset
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to rename file {file_id}: {e}")
            raise
    
    def replace_file(
        self,
        file_id: int,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        size_bytes: int,
        user_id: int,
        user_roles: List[str] = None
    ) -> FileAsset:
        """
        Replace file content (upload new file, delete old from storage).
        
        Authorization: Only LECTURER owner when version status is DRAFT.
        
        Args:
            file_id: File asset ID to replace
            file_bytes: New file content
            filename: New filename
            mime_type: New MIME type
            size_bytes: New file size
            user_id: User ID requesting replace
            user_roles: List of user roles
            
        Returns:
            Updated FileAsset
            
        Raises:
            ValueError: If file not found or validation fails
            UnauthorizedException: If user cannot edit file
            ValidationException: If version is not DRAFT
        """
        # Get existing file asset
        old_file_asset = self.repository.get_by_id(file_id)
        if not old_file_asset:
            raise ValueError(f'File {file_id} not found')
        
        # Get version info for authorization
        version_info = self.repository.get_version_info(old_file_asset.syllabus_version_id)
        if not version_info:
            raise ValueError(f'Syllabus version {old_file_asset.syllabus_version_id} not found')
        
        version_status, version_created_by = version_info
        
        # Authorization check
        if not can_edit_file(
            user_id=user_id,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            if version_status != WORKFLOW_DRAFT:
                raise ValidationException(
                    f'Cannot replace file. Syllabus version is {version_status}, not DRAFT'
                )
            raise UnauthorizedException(
                'Only the syllabus owner (LECTURER) can replace files in DRAFT status'
            )
        
        # Get syllabus_id for path organization
        syllabus_id = self.repository.get_version_syllabus_id(old_file_asset.syllabus_version_id)
        if syllabus_id is None:
            raise ValueError(f'Could not determine syllabus_id for version {old_file_asset.syllabus_version_id}')
        
        old_object_path = old_file_asset.object_path
        
        # Upload new file to Supabase
        new_object_path = None
        try:
            new_object_path, actual_size = self.storage_service.upload_file(
                file_data=file_bytes,
                syllabus_id=syllabus_id,
                version_id=old_file_asset.syllabus_version_id,
                original_filename=filename,
                mime_type=mime_type
            )
            size_bytes = actual_size
        except Exception as upload_error:
            logger.error(f"Supabase upload failed during replace: {upload_error}", exc_info=True)
            raise Exception("File upload to storage failed") from upload_error
        
        # Update database record
        try:
            # Update file content via repository
            file_asset = self.repository.update_file_content(
                file_id=file_id,
                original_filename=filename,
                object_path=new_object_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
                uploaded_by=user_id
            )
            
            self.session.commit()
            
            # Delete old file from Supabase (best-effort)
            try:
                self.storage_service.delete_file(old_object_path)
                logger.info(f"Deleted old file from storage: {old_object_path}")
            except Exception as delete_error:
                logger.warning(f"Failed to delete old file from storage: {delete_error}")
                # Don't fail the operation if cleanup fails
            
            logger.info(f"File {file_id} replaced successfully")
            return self.repository.get_by_id(file_id)
            
        except Exception as db_error:
            self.session.rollback()
            logger.error(f"Database operation failed after Supabase upload: {db_error}", exc_info=True)
            
            # Cleanup: delete new file from Supabase
            if new_object_path:
                try:
                    self.storage_service.delete_file(new_object_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup new file after DB error: {cleanup_error}")
            
            raise Exception("File replace failed") from db_error
    
    def delete_file(
        self,
        file_id: int,
        user_id: int,
        user_roles: List[str] = None
    ) -> None:
        """
        Delete a file (both from database and Supabase storage).
        
        Authorization: Only LECTURER owner when version status is DRAFT.
        
        Args:
            file_id: File asset ID
            user_id: User ID requesting delete
            user_roles: List of user roles
            
        Raises:
            ValueError: If file not found
            UnauthorizedException: If user cannot delete file
            ValidationException: If version is not DRAFT
        """
        # Get file asset
        file_asset = self.repository.get_by_id(file_id)
        if not file_asset:
            raise ValueError(f'File {file_id} not found')
        
        # Get version info for authorization
        version_info = self.repository.get_version_info(file_asset.syllabus_version_id)
        if not version_info:
            raise ValueError(f'Syllabus version {file_asset.syllabus_version_id} not found')
        
        version_status, version_created_by = version_info
        
        # Authorization check
        if not can_edit_file(
            user_id=user_id,
            user_roles=user_roles or [],
            version_workflow_status=version_status,
            version_created_by=version_created_by
        ):
            if version_status != WORKFLOW_DRAFT:
                raise ValidationException(
                    f'Cannot delete file. Syllabus version is {version_status}, not DRAFT'
                )
            raise UnauthorizedException(
                'Only the syllabus owner (LECTURER) can delete files in DRAFT status'
            )
        
        object_path = file_asset.object_path
        
        # Delete from database first
        try:
            self.repository.delete(file_id)
            self.session.commit()
            
            # Delete from Supabase storage (best-effort)
            try:
                self.storage_service.delete_file(object_path)
                logger.info(f"Deleted file from storage: {object_path}")
            except Exception as delete_error:
                logger.warning(f"Failed to delete file from storage: {delete_error}")
                # Don't fail if storage cleanup fails (file already removed from DB)
            
            logger.info(f"File {file_id} deleted successfully")
            
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as db_error:
            self.session.rollback()
            logger.exception(f"Failed to delete file {file_id}: {db_error}")
            raise
