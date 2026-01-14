from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class FileAsset(Base):
    """
    File metadata stored in MSSQL.
    Actual files are stored in Supabase Storage.
    """
    __tablename__ = 'file_asset'

    file_id = Column(Integer, primary_key=True, autoincrement=True)
    syllabus_version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    original_filename = Column(String(255), nullable=False)  # Original filename from upload
    display_name = Column(String(255), nullable=True)  # User-friendly display name (can be renamed)
    bucket = Column(String(100), nullable=False)  # Supabase bucket name
    object_path = Column(String(500), nullable=False)  # Path in Supabase Storage
    mime_type = Column(String(100), nullable=False)  # e.g., application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document
    size_bytes = Column(Integer, nullable=False)  # File size in bytes
    uploaded_by = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='file_assets')
    uploader = relationship('User', foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<FileAsset(file_id='{self.file_id}', original_filename='{self.original_filename}', object_path='{self.object_path}')>"
