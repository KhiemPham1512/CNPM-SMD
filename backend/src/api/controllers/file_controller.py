"""
File Upload/Download Controller

Handles file operations via Supabase Storage.
Backend acts as bridge between frontend and Supabase.
Follows Clean Architecture - controller only parses requests and returns responses.
"""
import logging
from typing import Tuple
from werkzeug.utils import secure_filename

from flask import Blueprint, Response, request, current_app

from api.responses import success_response, error_response, not_found_response
from api.utils.authz import token_required, get_user_id_from_token, role_required, get_user_roles
from api.utils.db import get_db_session
from dependency_container import container
from domain.constants import ROLE_LECTURER, ROLE_STUDENT
from domain.exceptions import UnauthorizedException, ValidationException

logger = logging.getLogger(__name__)

bp = Blueprint('file', __name__, url_prefix='/files')


@bp.route('/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """
    Health check endpoint for file storage status.
    ---
    get:
      summary: Check file storage configuration status
      tags:
        - Files
      responses:
        200:
          description: Storage status information
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: object
                    properties:
                      enabled:
                        type: boolean
                        description: Whether file storage is enabled
                      configured:
                        type: boolean
                        description: Whether storage is properly configured
                      provider:
                        type: string
                        example: "supabase"
                      bucket:
                        type: string
                        nullable: true
                        example: "syllabus-files"
                  message:
                    type: string
                    example: "File storage status"
    """
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    supabase_url = current_app.config.get('SUPABASE_URL')
    supabase_service_key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')
    supabase_bucket = current_app.config.get('SUPABASE_BUCKET', 'syllabus-files')
    
    # Check if configured (all required vars present)
    configured = bool(
        file_storage_enabled and 
        supabase_url and 
        supabase_service_key and 
        supabase_bucket
    )
    
    health_data = {
        'enabled': file_storage_enabled,
        'configured': configured,
        'provider': 'supabase' if file_storage_enabled else None,
        'bucket': supabase_bucket if file_storage_enabled else None
    }
    
    message = "File storage status"
    if not file_storage_enabled:
        message = "File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env to enable."
    elif not configured:
        missing = []
        if not supabase_url:
            missing.append('SUPABASE_URL')
        if not supabase_service_key:
            missing.append('SUPABASE_SERVICE_ROLE_KEY')
        if not supabase_bucket:
            missing.append('SUPABASE_BUCKET')
        message = f"File storage enabled but not configured. Missing: {', '.join(missing)}"
    else:
        message = "File storage is enabled and configured"
    
    return success_response(health_data, message), 200

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    mime_map = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword'
    }
    return mime_map.get(ext, 'application/octet-stream')


@bp.route('/upload', methods=['POST'])
@token_required
@role_required(ROLE_LECTURER)
def upload_file() -> Tuple[Response, int]:
    """
    Upload a file to Supabase Storage and save metadata to MSSQL.
    ---
    post:
      summary: Upload a file (PDF/DOCX) for a syllabus version
      security:
        - Bearer: []
      tags:
        - Files
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
                - syllabus_version_id
              properties:
                file:
                  type: string
                  format: binary
                  description: PDF or DOCX file
                syllabus_version_id:
                  type: integer
                  description: ID of the syllabus version
      responses:
        201:
          description: File uploaded successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/FileUploadResponse'
                  message:
                    type: string
                    example: "File uploaded successfully"
        400:
          description: Invalid input or file type not allowed
        404:
          description: Syllabus version not found
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
        500:
          description: Internal server error
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        # Parse and validate request
        if 'file' not in request.files:
            return error_response('No file provided', 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('No file selected', 400)
        
        # Validate file extension
        if not allowed_file(file.filename):
            return error_response(
                f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                400
            )
        
        # Get syllabus_version_id from form
        if 'syllabus_version_id' not in request.form:
            return error_response('syllabus_version_id is required', 400)
        
        try:
            syllabus_version_id = int(request.form['syllabus_version_id'])
        except ValueError:
            return error_response('syllabus_version_id must be an integer', 400)
        
        # Get current user
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Get user roles for defense-in-depth authorization check in service layer
        user_roles = get_user_roles(user_id, db)
        
        # Read file data
        file_data = file.read()
        if len(file_data) == 0:
            return error_response('File is empty', 400)
        
        # Check file size limit (in bytes)
        max_upload_bytes = current_app.config.get('MAX_UPLOAD_MB', 20) * 1024 * 1024
        if len(file_data) > max_upload_bytes:
            max_mb = current_app.config.get('MAX_UPLOAD_MB', 20)
            return error_response(
                f'File size exceeds maximum allowed size of {max_mb}MB',
                413  # Payload Too Large
            )
        
        # Get MIME type
        mime_type = file.content_type or get_mime_type(file.filename)
        if mime_type not in ALLOWED_MIME_TYPES:
            return error_response(f'MIME type not allowed: {mime_type}', 400)
        
        # Secure filename
        original_filename = secure_filename(file.filename)
        
        # Get optional display_name from form
        display_name = request.form.get('display_name', '').strip()
        if not display_name:
            display_name = original_filename
        
        # Call service layer (handles all business logic and transactions)
        file_service = container.file_service(db)
        file_asset = file_service.upload_file(
            version_id=syllabus_version_id,
            file_bytes=file_data,
            filename=original_filename,
            mime_type=mime_type,
            size_bytes=len(file_data),
            user_id=user_id,
            user_roles=user_roles,
            display_name=display_name
        )
        
        # Convert domain model to response format
        file_data_dict = {
            'file_id': file_asset.file_id,
            'syllabus_version_id': file_asset.syllabus_version_id,
            'original_filename': file_asset.original_filename,
            'display_name': file_asset.display_name,
            'bucket': file_asset.bucket,
            'object_path': file_asset.object_path,
            'mime_type': file_asset.mime_type,
            'size_bytes': file_asset.size_bytes,
            'uploaded_by': file_asset.uploaded_by,
            'created_at': file_asset.created_at
        }
        
        return success_response(data=file_data_dict, message='File uploaded successfully', status_code=201)
        
    except ValueError as e:
        # Validation errors from service layer
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except UnauthorizedException as e:
        # Authorization errors from service layer (defense-in-depth)
        return error_response(str(e), 403)
    except Exception as e:
        # Generic catch for unexpected errors
        logger.exception(f"Unexpected error uploading file: {e}")
        return error_response('File upload failed', 500)


@bp.route('/<int:file_id>/signed-url', methods=['GET'])
@token_required
def get_signed_url(file_id: int) -> Tuple[Response, int]:
    """
    Get a signed URL for downloading a file from Supabase Storage.
    ---
    get:
      summary: Get signed URL for file download
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the file
        - name: expires_in
          in: query
          required: false
          schema:
            type: integer
            default: 3600
          description: URL expiration time in seconds (default: 3600)
      responses:
        200:
          description: Signed URL generated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/FileSignedUrlResponse'
                  message:
                    type: string
                    example: "Signed URL generated successfully"
        404:
          description: File not found
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
        500:
          description: Internal server error
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        # Get expiration time from query parameter (default from config)
        expires_in = request.args.get('expires_in', type=int)
        if expires_in is None:
            expires_in = current_app.config.get('SUPABASE_SIGNED_URL_EXPIRES_IN', 3600)
        
        # Get current user
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        # Get user roles for authorization check in service layer
        user_roles = get_user_roles(user_id, db)
        
        # Call service layer
        file_service = container.file_service(db)
        signed_url, expires_in, object_path = file_service.get_signed_url(
            file_id=file_id,
            user_id=user_id,
            expires_in=expires_in,
            user_roles=user_roles
        )
        
        response_data = {
            'file_id': file_id,
            'signed_url': signed_url,
            'expires_in': expires_in,
            'object_path': object_path
        }
        
        return success_response(
            data=response_data,
            message='Signed URL generated successfully'
        )
        
    except ValueError as e:
        # Validation errors (e.g., file not found)
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except UnauthorizedException as e:
        # Authorization errors from service layer
        return error_response(str(e), 403)
    except Exception as e:
        # Generic catch for unexpected errors
        logger.exception(f"Error generating signed URL for file_id={file_id}: {e}")
        return error_response('Failed to generate signed URL', 500)


@bp.route('/<int:file_id>', methods=['GET'])
@token_required
def get_file_metadata(file_id: int) -> Tuple[Response, int]:
    """
    Get file metadata by ID.
    ---
    get:
      summary: Get file metadata
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the file
      responses:
        200:
          description: File metadata
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/FileUploadResponse'
                  message:
                    type: string
                    example: "File metadata retrieved successfully"
        404:
          description: File not found
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        # Get current user for authorization check
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db) if user_id else None
        
        # Call service layer
        file_service = container.file_service(db)
        file_asset = file_service.get_file_metadata(file_id, user_id=user_id, user_roles=user_roles)
        
        if not file_asset:
            return not_found_response(f'File {file_id} not found')
        
        # Convert domain model to response format
        file_data_dict = {
            'file_id': file_asset.file_id,
            'syllabus_version_id': file_asset.syllabus_version_id,
            'original_filename': file_asset.original_filename,
            'display_name': file_asset.display_name,
            'bucket': file_asset.bucket,
            'object_path': file_asset.object_path,
            'mime_type': file_asset.mime_type,
            'size_bytes': file_asset.size_bytes,
            'uploaded_by': file_asset.uploaded_by,
            'created_at': file_asset.created_at
        }
        
        return success_response(data=file_data_dict, message='File metadata retrieved successfully')
        
    except UnauthorizedException as e:
        # Authorization errors from service layer
        return error_response(str(e), 403)
    except Exception as e:
        # Generic catch for unexpected errors (read-only operation, no rollback needed)
        logger.exception(f"Error getting file metadata for file_id={file_id}: {e}")
        return error_response('Failed to retrieve file metadata', 500)


@bp.route('/version/<int:version_id>', methods=['GET'])
@token_required
def list_files_by_version(version_id: int) -> Tuple[Response, int]:
    """
    Get all files for a syllabus version.
    ---
    get:
      summary: List all files for a syllabus version
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: version_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus version
      responses:
        200:
          description: List of files
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/FileUploadResponse'
                  message:
                    type: string
                    example: "Files retrieved successfully"
        503:
          description: File storage is disabled
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        # Get current user for authorization check
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db) if user_id else None
        
        # Call service layer
        file_service = container.file_service(db)
        files = file_service.list_files_by_version(version_id, user_id=user_id, user_roles=user_roles)
        
        # Convert domain models to response format
        files_data = [
            {
                'file_id': f.file_id,
                'syllabus_version_id': f.syllabus_version_id,
                'original_filename': f.original_filename,
                'display_name': f.display_name,
                'bucket': f.bucket,
                'object_path': f.object_path,
                'mime_type': f.mime_type,
                'size_bytes': f.size_bytes,
                'uploaded_by': f.uploaded_by,
                'created_at': f.created_at
            }
            for f in files
        ]
        
        return success_response(data=files_data, message='Files retrieved successfully')
        
    except ValueError as e:
        # Validation errors (e.g., version not found)
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except UnauthorizedException as e:
        # Authorization errors from service layer
        return error_response(str(e), 403)
    except Exception as e:
        # Generic catch for unexpected errors (read-only operation, no rollback needed)
        logger.exception(f"Error listing files for version_id={version_id}: {e}")
        return error_response('Failed to retrieve files', 500)


@bp.route('/<int:file_id>', methods=['PATCH'])
@token_required
@role_required(ROLE_LECTURER)
def rename_file(file_id: int) -> Tuple[Response, int]:
    """
    Rename display_name of a file.
    ---
    patch:
      summary: Rename file display name (LECTURER owner, DRAFT only)
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - display_name
              properties:
                display_name:
                  type: string
                  example: "Syllabus Document v2"
      responses:
        200:
          description: File renamed successfully
        403:
          description: Forbidden - not owner or not DRAFT
        409:
          description: Conflict - version is not DRAFT
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        data = request.get_json()
        if not data or 'display_name' not in data:
            return error_response('display_name is required', 400)
        
        display_name = data['display_name'].strip()
        if not display_name:
            return error_response('display_name cannot be empty', 400)
        
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_roles = get_user_roles(user_id, db)
        
        file_service = container.file_service(db)
        file_asset = file_service.rename_file(
            file_id=file_id,
            display_name=display_name,
            user_id=user_id,
            user_roles=user_roles
        )
        
        file_data_dict = {
            'file_id': file_asset.file_id,
            'syllabus_version_id': file_asset.syllabus_version_id,
            'original_filename': file_asset.original_filename,
            'display_name': file_asset.display_name,
            'bucket': file_asset.bucket,
            'object_path': file_asset.object_path,
            'mime_type': file_asset.mime_type,
            'size_bytes': file_asset.size_bytes,
            'uploaded_by': file_asset.uploaded_by,
            'created_at': file_asset.created_at
        }
        
        return success_response(data=file_data_dict, message='File renamed successfully')
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except ValidationException as e:
        return error_response(str(e), 409)
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    except Exception as e:
        logger.exception(f"Error renaming file {file_id}: {e}")
        return error_response('Failed to rename file', 500)


@bp.route('/<int:file_id>/replace', methods=['POST'])
@token_required
@role_required(ROLE_LECTURER)
def replace_file(file_id: int) -> Tuple[Response, int]:
    """
    Replace file content (upload new file, delete old).
    ---
    post:
      summary: Replace file content (LECTURER owner, DRAFT only)
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
      responses:
        200:
          description: File replaced successfully
        403:
          description: Forbidden - not owner or not DRAFT
        409:
          description: Conflict - version is not DRAFT
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        if 'file' not in request.files:
            return error_response('No file provided', 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('No file selected', 400)
        
        if not allowed_file(file.filename):
            return error_response(
                f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                400
            )
        
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_roles = get_user_roles(user_id, db)
        
        file_data = file.read()
        if len(file_data) == 0:
            return error_response('File is empty', 400)
        
        max_upload_bytes = current_app.config.get('MAX_UPLOAD_MB', 20) * 1024 * 1024
        if len(file_data) > max_upload_bytes:
            max_mb = current_app.config.get('MAX_UPLOAD_MB', 20)
            return error_response(
                f'File size exceeds maximum allowed size of {max_mb}MB',
                413
            )
        
        mime_type = file.content_type or get_mime_type(file.filename)
        if mime_type not in ALLOWED_MIME_TYPES:
            return error_response(f'MIME type not allowed: {mime_type}', 400)
        
        original_filename = secure_filename(file.filename)
        
        file_service = container.file_service(db)
        file_asset = file_service.replace_file(
            file_id=file_id,
            file_bytes=file_data,
            filename=original_filename,
            mime_type=mime_type,
            size_bytes=len(file_data),
            user_id=user_id,
            user_roles=user_roles
        )
        
        file_data_dict = {
            'file_id': file_asset.file_id,
            'syllabus_version_id': file_asset.syllabus_version_id,
            'original_filename': file_asset.original_filename,
            'display_name': file_asset.display_name,
            'bucket': file_asset.bucket,
            'object_path': file_asset.object_path,
            'mime_type': file_asset.mime_type,
            'size_bytes': file_asset.size_bytes,
            'uploaded_by': file_asset.uploaded_by,
            'created_at': file_asset.created_at
        }
        
        return success_response(data=file_data_dict, message='File replaced successfully')
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except ValidationException as e:
        return error_response(str(e), 409)
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    except Exception as e:
        logger.exception(f"Error replacing file {file_id}: {e}")
        return error_response('Failed to replace file', 500)


@bp.route('/<int:file_id>', methods=['DELETE'])
@token_required
@role_required(ROLE_LECTURER)
def delete_file(file_id: int) -> Tuple[Response, int]:
    """
    Delete a file.
    ---
    delete:
      summary: Delete file (LECTURER owner, DRAFT only)
      security:
        - Bearer: []
      tags:
        - Files
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: File deleted successfully
        403:
          description: Forbidden - not owner or not DRAFT
        409:
          description: Conflict - version is not DRAFT
        503:
          description: File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env
    """
    # Check if file storage is enabled
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        return error_response(
            'File storage is disabled. Set FILE_STORAGE_ENABLED=true in .env',
            503
        )
    
    db = get_db_session()
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_roles = get_user_roles(user_id, db)
        
        file_service = container.file_service(db)
        file_service.delete_file(
            file_id=file_id,
            user_id=user_id,
            user_roles=user_roles
        )
        
        return success_response(message='File deleted successfully')
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except ValidationException as e:
        return error_response(str(e), 409)
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    except Exception as e:
        logger.exception(f"Error deleting file {file_id}: {e}")
        return error_response('Failed to delete file', 500)
