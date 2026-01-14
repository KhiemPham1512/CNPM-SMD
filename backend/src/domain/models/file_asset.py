from datetime import datetime


class FileAsset:
    """
    Domain model for file asset metadata.
    Represents file metadata stored in database.
    """
    def __init__(
        self,
        file_id: int = None,
        syllabus_version_id: int = None,
        original_filename: str = None,
        display_name: str = None,
        bucket: str = None,
        object_path: str = None,
        mime_type: str = None,
        size_bytes: int = None,
        uploaded_by: int = None,
        created_at: datetime = None
    ):
        self.file_id = file_id
        self.syllabus_version_id = syllabus_version_id
        self.original_filename = original_filename
        self.display_name = display_name  # User-friendly name (can be renamed)
        self.bucket = bucket
        self.object_path = object_path
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.uploaded_by = uploaded_by
        self.created_at = created_at
