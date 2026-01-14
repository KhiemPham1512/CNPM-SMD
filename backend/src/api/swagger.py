from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from flask_restx import Model
from flask_restx.fields import String, Integer, Raw

# Initialize APISpec (without MarshmallowPlugin)
spec = APISpec(
    title="SMD API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin()],
)

# Flask-RESTX Models for API Documentation (NOT for validation)
# These models align with Marshmallow schemas but are separate

# User Models
UserRequest = Model('UserRequest', {
    'username': String(required=True, description='Username'),
    'password': String(required=True, description='Password (plain text - will be hashed by service)'),
    'full_name': String(required=True, description='Full name'),
    'email': String(required=True, description='Email address'),
    'status': String(required=False, default='active', description='User status'),
})

UserResponse = Model('UserResponse', {
    'user_id': Integer(required=True, description='User ID'),
    'username': String(required=True, description='Username'),
    # password_hash removed - security: never expose password hash in API response
    'full_name': String(required=True, description='Full name'),
    'email': String(required=True, description='Email address'),
    'status': String(required=True, description='User status'),
    'created_at': Raw(required=True, description='Creation timestamp'),
})

UserUpdateStatus = Model('UserUpdateStatus', {
    'status': String(required=True, description='User status'),
})

# Syllabus Models
SyllabusCreate = Model('SyllabusCreate', {
    'subject_id': Integer(required=True, description='Subject ID'),
    'program_id': Integer(required=True, description='Program ID'),
    # owner_lecturer_id is NOT in request - it's taken from JWT token
})

SyllabusCreateResponse = Model('SyllabusCreateResponse', {
    'syllabus_id': Integer(required=True, description='Syllabus ID'),
    'draft_version_id': Integer(required=True, description='Draft version ID created with the syllabus'),
})

SyllabusUpdate = Model('SyllabusUpdate', {
    'subject_id': Integer(required=False, description='Subject ID'),
    'program_id': Integer(required=False, description='Program ID'),
    'owner_lecturer_id': Integer(required=False, description='Owner lecturer ID'),
})

SyllabusResponse = Model('SyllabusResponse', {
    'syllabus_id': Integer(required=True, description='Syllabus ID'),
    'subject_id': Integer(required=True, description='Subject ID'),
    'program_id': Integer(required=True, description='Program ID'),
    'owner_lecturer_id': Integer(required=True, description='Owner lecturer ID'),
    'current_version_id': Integer(required=False, description='Current version ID', allow_none=True),
    'lifecycle_status': String(required=True, description='Lifecycle status'),
    'created_at': Raw(required=True, description='Creation timestamp'),
})

# File Models
FileUploadResponse = Model('FileUploadResponse', {
    'file_id': Integer(required=True, description='File ID'),
    'syllabus_version_id': Integer(required=True, description='Syllabus version ID'),
    'original_filename': String(required=True, description='Original filename'),
    'bucket': String(required=True, description='Supabase bucket name'),
    'object_path': String(required=True, description='Path in Supabase Storage'),
    'mime_type': String(required=True, description='MIME type'),
    'size_bytes': Integer(required=True, description='File size in bytes'),
    'uploaded_by': Integer(required=True, description='User ID who uploaded the file'),
    'created_at': Raw(required=True, description='Upload timestamp'),
})

FileSignedUrlResponse = Model('FileSignedUrlResponse', {
    'file_id': Integer(required=True, description='File ID'),
    'signed_url': String(required=True, description='Signed URL for file download'),
    'expires_in': Integer(required=True, description='URL expiration time in seconds'),
    'object_path': String(required=True, description='Path in Supabase Storage'),
})

# Convert Flask-RESTX field to OpenAPI 3 schema
def convert_restx_field_to_openapi(field_name, field):
    """
    Convert a Flask-RESTX field to OpenAPI 3.0 schema format.
    
    Args:
        field_name: Name of the field
        field: Flask-RESTX field instance
    
    Returns:
        dict: OpenAPI 3.0 field schema
    """
    field_schema = {}
    
    # Determine field type and format
    if isinstance(field, Integer):
        field_schema['type'] = 'integer'
    elif isinstance(field, Raw):
        # Raw fields used for timestamps (created_at, updated_at) should be date-time
        if field_name in ('created_at', 'updated_at'):
            field_schema['type'] = 'string'
            field_schema['format'] = 'date-time'
        else:
            # Other Raw fields default to object
            field_schema['type'] = 'object'
    elif isinstance(field, String):
        field_schema['type'] = 'string'
        # Check if this is an email field (by field name or description)
        if field_name == 'email' or (hasattr(field, 'description') and 
                                     field.description and 'email' in field.description.lower()):
            field_schema['format'] = 'email'
    else:
        # Default to string for unknown types
        field_schema['type'] = 'string'
    
    # Add nullable if allow_none is True
    if hasattr(field, 'allow_none') and field.allow_none:
        field_schema['nullable'] = True
    
    # Add default value if present
    if hasattr(field, 'default') and field.default is not None:
        field_schema['default'] = field.default
    
    # Add description if present
    if hasattr(field, 'description') and field.description:
        field_schema['description'] = field.description
    
    return field_schema


# Register models with APISpec
# Convert Flask-RESTX models to OpenAPI schema format
def register_restx_model(spec, model_name, restx_model):
    """
    Register a Flask-RESTX model with APISpec.
    
    Converts Flask-RESTX Model to OpenAPI 3.0 schema format without
    relying on __schema__ property.
    
    Args:
        spec: APISpec instance
        model_name: Name for the schema in OpenAPI spec
        restx_model: Flask-RESTX Model instance
    """
    properties = {}
    required_fields = []
    
    # Iterate through all fields in the model
    for field_name, field in restx_model.items():
        # Convert field to OpenAPI schema
        field_schema = convert_restx_field_to_openapi(field_name, field)
        properties[field_name] = field_schema
        
        # Collect required fields
        if hasattr(field, 'required') and field.required:
            required_fields.append(field_name)
    
    # Build OpenAPI 3.0 object schema
    openapi_schema = {
        'type': 'object',
        'properties': properties
    }
    
    # Add required array if there are required fields
    if required_fields:
        openapi_schema['required'] = required_fields
    
    # Register schema with APISpec
    spec.components.schema(model_name, openapi_schema)

# Register all models
register_restx_model(spec, "UserRequest", UserRequest)
register_restx_model(spec, "UserResponse", UserResponse)
register_restx_model(spec, "UserUpdateStatus", UserUpdateStatus)
register_restx_model(spec, "SyllabusCreate", SyllabusCreate)
register_restx_model(spec, "SyllabusCreateResponse", SyllabusCreateResponse)
register_restx_model(spec, "SyllabusUpdate", SyllabusUpdate)
register_restx_model(spec, "SyllabusResponse", SyllabusResponse)
register_restx_model(spec, "FileUploadResponse", FileUploadResponse)
register_restx_model(spec, "FileSignedUrlResponse", FileSignedUrlResponse)

# Security scheme for JWT
# OpenAPI 3.0 HTTP Bearer scheme - Swagger UI will automatically add "Bearer " prefix
# Users should enter ONLY the raw token (without "Bearer " prefix) in the Authorize modal
spec.components.security_scheme("Bearer", {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": "JWT Authorization header. Enter only the token (without 'Bearer ' prefix). Swagger UI will automatically add 'Bearer ' prefix to the Authorization header."
})


# Helper function to get OpenAPI spec as dictionary
def get_openapi_spec():
    """
    Get the OpenAPI specification as a dictionary.
    
    Returns:
        dict: OpenAPI 3.0 specification dictionary
    """
    return spec.to_dict()