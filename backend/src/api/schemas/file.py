from marshmallow import Schema, fields


class FileUploadResponseSchema(Schema):
    """Schema for file upload response."""
    file_id = fields.Int(required=True)
    syllabus_version_id = fields.Int(required=True)
    original_filename = fields.Str(required=True)
    bucket = fields.Str(required=True)
    object_path = fields.Str(required=True)
    mime_type = fields.Str(required=True)
    size_bytes = fields.Int(required=True)
    uploaded_by = fields.Int(required=True)
    created_at = fields.Raw(required=True)


class FileSignedUrlResponseSchema(Schema):
    """Schema for signed URL response."""
    file_id = fields.Int(required=True)
    signed_url = fields.Str(required=True)
    expires_in = fields.Int(required=True)
    object_path = fields.Str(required=True)
