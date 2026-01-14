import logging
from typing import Tuple, Dict, Any
from flask import Blueprint, Response, request
from api.responses import success_response, error_response, not_found_response, validation_error_response
from api.schemas.user import RoleAssignmentSchema
from api.utils.authz import token_required, role_required, get_user_id_from_token
from api.utils.db import get_db_session
from dependency_container import container
from domain.exceptions import ValidationException
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')

ROLE_ADMIN = 'ADMIN'


@bp.route('/users', methods=['GET'])
@token_required
@role_required(ROLE_ADMIN)
def list_users_admin() -> Tuple[Response, int]:
    """
    Get all users (Admin only)
    ---
    get:
      summary: Get all users (Admin only)
      security:
        - Bearer: []
      tags:
        - Admin
      responses:
        200:
          description: List of users
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
                      type: object
                  message:
                    type: string
                    example: "Users retrieved successfully"
        401:
          description: Unauthorized
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        users = user_service.list_users()
        # Convert to dict for response
        users_data = []
        for user in users:
            user_dict = {
                'user_id': user.user_id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            }
            # Get roles for each user
            try:
                roles = user_service.get_user_roles(user.user_id)
                user_dict['roles'] = roles
            except Exception as e:
                logger.warning(f"Failed to get roles for user {user.user_id}: {e}")
                user_dict['roles'] = []
            users_data.append(user_dict)
        
        return success_response(data=users_data, message='Users retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing users: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve users', 500)


@bp.route('/users/<int:user_id>', methods=['PATCH'])
@token_required
@role_required(ROLE_ADMIN)
def update_user_admin(user_id: int) -> Tuple[Response, int]:
    """
    Update user (lock/unlock or other fields) - Admin only
    ---
    patch:
      summary: Update user (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: user_id
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
              properties:
                status:
                  type: string
                  enum: [active, inactive]
      tags:
        - Admin
      responses:
        200:
          description: User updated successfully
        400:
          description: Invalid input
        404:
          description: User not found
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        data = request.get_json() or {}
        
        # Support status update (lock/unlock)
        if 'status' in data:
            status = data['status']
            if status not in ['active', 'inactive']:
                return validation_error_response({
                    'status': ['Status must be "active" or "inactive"']
                })
            user = user_service.update_user_status(user_id, status)
            from api.schemas.user import UserResponseSchema
            response_schema = UserResponseSchema()
            user_data = response_schema.dump(user)
            return success_response(data=user_data, message='User status updated successfully')
        
        return error_response('No valid fields to update', 400)
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error updating user {user_id}: {e}")
        return error_response('Failed to update user', 500)


@bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@token_required
@role_required(ROLE_ADMIN)
def assign_roles(user_id: int) -> Tuple[Response, int]:
    """
    Assign multiple roles to a user (replace existing) - Admin only
    ---
    put:
      summary: Assign roles to a user (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: user_id
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
                - roles
              properties:
                roles:
                  type: array
                  items:
                    type: string
                    enum: [ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT]
      tags:
        - Admin
      responses:
        200:
          description: Roles assigned successfully
        400:
          description: Invalid input
        404:
          description: User not found
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        data = request.get_json() or {}
        
        # Use Marshmallow schema for validation
        from api.schemas.user import RoleAssignmentSchema
        role_schema = RoleAssignmentSchema()
        errors = role_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        roles = [r.upper() for r in data['roles']]
        
        # Assign all roles (service will handle replacing existing)
        user = user_service.assign_roles(user_id, roles)
        from api.schemas.user import UserResponseSchema
        response_schema = UserResponseSchema()
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='Roles assigned successfully')
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error assigning roles to user {user_id}: {e}")
        return error_response('Failed to assign roles', 500)


@bp.route('/system-settings', methods=['GET'])
@token_required
@role_required(ROLE_ADMIN)
def get_system_settings() -> Tuple[Response, int]:
    """
    Get all system settings - Admin only
    ---
    get:
      summary: Get all system settings (Admin only)
      security:
        - Bearer: []
      tags:
        - Admin
      responses:
        200:
          description: System settings retrieved successfully
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
                    additionalProperties:
                      type: string
                    example:
                      FILE_STORAGE_ENABLED: "true"
                      ACADEMIC_YEAR: "2024-2025"
                  message:
                    type: string
                    example: "System settings retrieved successfully"
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        from infrastructure.models.system_setting import SystemSetting
        settings = db.query(SystemSetting).all()
        
        # Convert to key-value dict
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.key] = setting.value
        
        # Add default settings if not in DB
        from config import Config
        if 'FILE_STORAGE_ENABLED' not in settings_dict:
            settings_dict['FILE_STORAGE_ENABLED'] = str(Config.FILE_STORAGE_ENABLED).lower()
        
        return success_response(data=settings_dict, message='System settings retrieved successfully')
    except Exception as e:
        logger.exception(f"Error getting system settings: {e}")
        return error_response('Failed to retrieve system settings', 500)


@bp.route('/system-settings', methods=['PUT'])
@token_required
@role_required(ROLE_ADMIN)
def update_system_settings() -> Tuple[Response, int]:
    """
    Update system settings - Admin only
    ---
    put:
      summary: Update system settings (Admin only)
      security:
        - Bearer: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              additionalProperties:
                type: string
              example:
                FILE_STORAGE_ENABLED: "true"
                ACADEMIC_YEAR: "2024-2025"
      tags:
        - Admin
      responses:
        200:
          description: System settings updated successfully
        400:
          description: Invalid input
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        from infrastructure.models.system_setting import SystemSetting
        from datetime import datetime, timezone
        user_id = get_user_id_from_token()
        
        data = request.get_json() or {}
        if not data:
            return error_response('Settings data is required', 400)
        
        updated_settings = {}
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return error_response(f'Invalid setting: {key} must be string key-value pair', 400)
            
            # Find or create setting
            setting = db.query(SystemSetting).filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                setting.updated_at = datetime.now(timezone.utc)
                setting.updated_by = user_id
            else:
                setting = SystemSetting(
                    key=key,
                    value=str(value),
                    data_type='string',  # Default type
                    updated_at=datetime.now(timezone.utc),
                    updated_by=user_id
                )
                db.add(setting)
            
            updated_settings[key] = str(value)
        
        db.commit()
        return success_response(data=updated_settings, message='System settings updated successfully')
    except IntegrityError as e:
        db.rollback()
        logger.exception(f"IntegrityError updating system settings: {e}")
        return error_response('Failed to update system settings due to constraint violation', 400)
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating system settings: {e}")
        return error_response('Failed to update system settings', 500)


@bp.route('/publishing', methods=['GET'])
@token_required
@role_required(ROLE_ADMIN)
def list_published() -> Tuple[Response, int]:
    """
    Get all published syllabi - Admin only
    ---
    get:
      summary: Get all published syllabi (Admin only)
      security:
        - Bearer: []
      tags:
        - Admin
      responses:
        200:
          description: Published syllabi retrieved successfully
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
                      type: object
                  message:
                    type: string
                    example: "Published syllabi retrieved successfully"
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        published_syllabi = syllabus_service.list_syllabi_by_status('PUBLISHED')
        
        # Convert to dict with version info
        from api.schemas.syllabus import SyllabusResponseSchema
        response_schema = SyllabusResponseSchema()
        syllabi_data = response_schema.dump(published_syllabi, many=True)
        
        return success_response(data=syllabi_data, message='Published syllabi retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing published syllabi: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve published syllabi', 500)


@bp.route('/publishing/<int:version_id>/unpublish', methods=['POST'])
@token_required
@role_required(ROLE_ADMIN)
def unpublish_version(version_id: int) -> Tuple[Response, int]:
    """
    Unpublish a syllabus version - Admin only
    ---
    post:
      summary: Unpublish a syllabus version (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: version_id
          in: path
          required: true
          schema:
            type: integer
      tags:
        - Admin
      responses:
        200:
          description: Syllabus unpublished successfully
        404:
          description: Version not found
        400:
          description: Invalid status
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        from infrastructure.models.syllabus_version import SyllabusVersion
        version = db.query(SyllabusVersion).filter_by(version_id=version_id).first()
        if not version:
            return not_found_response(f'Syllabus version {version_id} not found')
        
        if version.workflow_status != 'PUBLISHED':
            return error_response(f'Version is not PUBLISHED. Current status: {version.workflow_status}', 400)
        
        syllabus_service = container.syllabus_service(db)
        user_roles = ['ADMIN']  # Admin can always unpublish
        syllabus = syllabus_service.unpublish(version.syllabus_id, 'ADMIN')
        
        from api.schemas.syllabus import SyllabusResponseSchema
        response_schema = SyllabusResponseSchema()
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus unpublished successfully')
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error unpublishing version {version_id}: {e}")
        return error_response('Failed to unpublish syllabus', 500)


@bp.route('/publishing/<int:version_id>/archive', methods=['POST'])
@token_required
@role_required(ROLE_ADMIN)
def archive_version(version_id: int) -> Tuple[Response, int]:
    """
    Archive a syllabus version - Admin only
    ---
    post:
      summary: Archive a syllabus version (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: version_id
          in: path
          required: true
          schema:
            type: integer
      tags:
        - Admin
      responses:
        200:
          description: Syllabus archived successfully
        404:
          description: Version not found
        400:
          description: Invalid status
        403:
          description: Forbidden (Admin required)
    """
    db = get_db_session()
    try:
        from infrastructure.models.syllabus_version import SyllabusVersion
        from datetime import datetime, timezone
        
        version = db.query(SyllabusVersion).filter_by(version_id=version_id).first()
        if not version:
            return not_found_response(f'Syllabus version {version_id} not found')
        
        # Archive: Set status to a special "ARCHIVED" status or keep PUBLISHED but mark as archived
        # For now, we'll use a simple approach: update workflow_status to "ARCHIVED" if it exists
        # Otherwise, we can add a flag or use a different approach
        
        # Check if ARCHIVED is a valid status in the system
        # For stub: we'll just update the version status to a special value
        # In a full implementation, you might have an ARCHIVED status or an is_archived flag
        
        # Stub implementation: For now, we'll just return success
        # In a real system, you'd update the version status or add an archived flag
        
        return success_response(
            data={'version_id': version_id, 'status': 'archived'},
            message='Syllabus version archived successfully (stub - full implementation pending)'
        )
    except Exception as e:
        logger.exception(f"Error archiving version {version_id}: {e}")
        return error_response('Failed to archive syllabus version', 500)
