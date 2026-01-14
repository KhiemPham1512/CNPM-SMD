from abc import ABC, abstractmethod
from typing import List, Optional
from .file_asset import FileAsset


class IFileRepository(ABC):
    """Interface for file asset repository operations."""
    
    @abstractmethod
    def create(self, file_asset: FileAsset) -> FileAsset:
        """
        Create a new file asset record.
        Does NOT commit - transaction managed by service layer.
        
        Args:
            file_asset: FileAsset domain model
            
        Returns:
            FileAsset with file_id populated
        """
        pass
    
    @abstractmethod
    def get_by_id(self, file_id: int) -> Optional[FileAsset]:
        """
        Get file asset by ID.
        
        Args:
            file_id: File asset ID
            
        Returns:
            FileAsset if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_by_version(self, version_id: int) -> List[FileAsset]:
        """
        List all file assets for a syllabus version.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            List of FileAsset objects
        """
        pass
    
    @abstractmethod
    def delete(self, file_id: int) -> None:
        """
        Delete file asset by ID.
        Does NOT commit - transaction managed by service layer.
        
        Args:
            file_id: File asset ID
            
        Raises:
            ValueError: If file not found
        """
        pass
    
    @abstractmethod
    def verify_version_exists(self, version_id: int) -> bool:
        """
        Verify that a syllabus version exists.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            True if version exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_version_syllabus_id(self, version_id: int) -> Optional[int]:
        """
        Get syllabus_id for a given version_id.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            Syllabus ID if version exists, None otherwise
        """
        pass
    
    @abstractmethod
    def get_version_workflow_status(self, version_id: int) -> Optional[str]:
        """
        Get workflow_status for a given version_id.
        Used for authorization checks (e.g., deny student unless published).
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            Workflow status if version exists, None otherwise
        """
        pass
    
    @abstractmethod
    def get_version_info(self, version_id: int) -> Optional[tuple]:
        """
        Get version info (workflow_status, created_by) for authorization checks.
        
        Args:
            version_id: Syllabus version ID
            
        Returns:
            Tuple of (workflow_status, created_by) if version exists, None otherwise
        """
        pass
    
    @abstractmethod
    def update_display_name(self, file_id: int, display_name: str) -> FileAsset:
        """
        Update display_name of a file asset.
        Does NOT commit - transaction managed by service layer.
        
        Args:
            file_id: File asset ID
            display_name: New display name
            
        Returns:
            Updated FileAsset
            
        Raises:
            ValueError: If file not found
        """
        pass
    
    @abstractmethod
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
        
        Args:
            file_id: File asset ID
            original_filename: New original filename
            object_path: New object path in storage
            mime_type: New MIME type
            size_bytes: New file size
            uploaded_by: User ID who replaced the file
            
        Returns:
            Updated FileAsset
            
        Raises:
            ValueError: If file not found
        """
        pass
