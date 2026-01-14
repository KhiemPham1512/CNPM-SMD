"""
Supabase Storage Service

Handles file upload, download, and signed URL generation for Supabase Storage.
Backend acts as the bridge - frontend never talks directly to Supabase.
"""
import logging
import os
import uuid
from typing import Optional, Tuple
from pathlib import Path

from supabase import create_client, Client
from flask import current_app

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Service for interacting with Supabase Storage.
    Uses service_role key for backend operations.
    """
    
    def __init__(self, supabase_url: str, service_role_key: str, bucket: str = 'syllabus-files'):
        """
        Initialize Supabase Storage client.
        
        Args:
            supabase_url: Supabase project URL (e.g., http://localhost:8000)
            service_role_key: Supabase service_role key (from .env)
            bucket: Storage bucket name (default: 'syllabus-files')
        """
        if not supabase_url or not service_role_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(supabase_url, service_role_key)
        self.bucket = bucket
        logger.info(f"Initialized Supabase Storage client for bucket: {bucket}")
    
    def upload_file(
        self,
        file_data: bytes,
        syllabus_id: int,
        version_id: int,
        original_filename: str,
        mime_type: str
    ) -> Tuple[str, int]:
        """
        Upload file to Supabase Storage.
        
        Args:
            file_data: File content as bytes
            syllabus_id: Syllabus ID for path organization
            version_id: Version ID for path organization
            original_filename: Original filename (for extension)
            mime_type: MIME type of the file
        
        Returns:
            Tuple of (object_path, size_bytes)
        
        Raises:
            Exception: If upload fails
        """
        # Generate unique filename with UUID
        file_ext = Path(original_filename).suffix.lower()
        if not file_ext:
            # Default extension based on mime_type
            if 'pdf' in mime_type:
                file_ext = '.pdf'
            elif 'wordprocessingml' in mime_type or 'msword' in mime_type:
                file_ext = '.docx'
            else:
                file_ext = '.bin'
        
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        object_path = f"syllabi/{syllabus_id}/versions/{version_id}/{unique_filename}"
        
        try:
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket).upload(
                path=object_path,
                file=file_data,
                file_options={
                    "content-type": mime_type,
                    "upsert": False  # Don't overwrite existing files
                }
            )
            
            size_bytes = len(file_data)
            logger.info(f"Uploaded file to Supabase: {object_path} ({size_bytes} bytes)")
            
            return object_path, size_bytes
            
        except Exception as e:
            # Log error without exposing internal details
            error_msg = str(e)
            # Don't expose full exception in user-facing messages
            logger.error(f"Failed to upload file to Supabase: {error_msg}", exc_info=True)
            # Raise generic exception (internal details logged above)
            raise Exception("File upload to storage failed")
    
    def get_signed_url(self, object_path: str, expires_in: int = 3600) -> str:
        """
        Generate a signed URL for private file access.
        
        Args:
            object_path: Path to file in Supabase Storage
            expires_in: URL expiration time in seconds (default: 3600 = 1 hour)
        
        Returns:
            Signed URL string
        
        Raises:
            Exception: If URL generation fails
        """
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(
                path=object_path,
                expires_in=expires_in
            )
            
            # Handle different response formats
            if isinstance(response, str):
                signed_url = response
            elif isinstance(response, dict):
                signed_url = response.get('signedURL') or response.get('signedUrl') or response.get('url')
            else:
                # Try to get attribute if it's an object
                signed_url = getattr(response, 'signedURL', None) or getattr(response, 'signedUrl', None) or getattr(response, 'url', None)
            
            if not signed_url:
                # Don't expose response object in error message
                logger.error(f"Supabase did not return a signed URL for {object_path}")
                raise ValueError("Supabase did not return a signed URL")
            
            logger.debug(f"Generated signed URL for: {object_path} (expires in {expires_in}s)")
            return signed_url
            
        except Exception as e:
            # Log error without exposing internal details
            error_msg = str(e)
            logger.error(f"Failed to generate signed URL for {object_path}: {error_msg}", exc_info=True)
            # Raise generic exception (internal details logged above)
            raise Exception("Failed to generate signed URL")
    
    def delete_file(self, object_path: str) -> bool:
        """
        Delete file from Supabase Storage.
        
        Args:
            object_path: Path to file in Supabase Storage
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.storage.from_(self.bucket).remove([object_path])
            logger.info(f"Deleted file from Supabase: {object_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Supabase {object_path}: {str(e)}", exc_info=True)
            return False
    
    def delete_object(self, object_path: str) -> bool:
        """
        Alias for delete_file for consistency.
        Delete file from Supabase Storage (best-effort cleanup).
        
        Args:
            object_path: Path to file in Supabase Storage
        
        Returns:
            True if successful, False otherwise (logs error but doesn't raise)
        """
        return self.delete_file(object_path)


def get_supabase_storage_service() -> SupabaseStorageService:
    """
    Factory function to get SupabaseStorageService from Flask app config.
    
    Returns:
        SupabaseStorageService instance
        
    Raises:
        ValueError: If Supabase configuration is missing or file storage is disabled
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        raise ValueError(
            "File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env file to enable."
        )
    
    supabase_url = current_app.config.get('SUPABASE_URL')
    service_role_key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')
    bucket = current_app.config.get('SUPABASE_BUCKET', 'syllabus-files')
    
    if not supabase_url or not service_role_key:
        raise ValueError(
            "Supabase configuration missing. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env file."
        )
    
    return SupabaseStorageService(supabase_url, service_role_key, bucket)
