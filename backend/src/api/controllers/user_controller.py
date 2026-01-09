import logging
from typing import Tuple

from flask import Blueprint, Response, jsonify, request

from api.schemas.user import UserRequestSchema, UserResponseSchema, UserUpdateStatusSchema
from api.responses import success_response, error_response, not_found_response, validation_error_response
from api.utils.authz import token_required, role_required
from api.utils.db import get_db_session
from dependency_container import container

logger = logging.getLogger(__name__)

bp = Blueprint('user', __name__, url_prefix='/users')

request_schema = UserRequestSchema()
response_schema = UserResponseSchema()
update_status_schema = UserUpdateStatusSchema()


@bp.route('/', methods=['GET'])
@token_required
def list_users() -> Tuple[Response, int]:
    """
    Get all users
    ---
    get:
      summary: Get all users
      security:
        - Bearer: []
      tags:
        - Users
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
                      $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "Users retrieved successfully"
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        users = user_service.list_users()
        users_data = response_schema.dump(users, many=True)
        return success_response(data=users_data, message='Users retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing users: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve users', 500)


@bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id: int) -> Tuple[Response, int]:
    """
    Get user by id
    ---
    get:
      summary: Get user by id
      security:
        - Bearer: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the user
      tags:
        - Users
      responses:
        200:
          description: User object
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "User retrieved successfully"
        404:
          description: User not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            return not_found_response('User not found')
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='User retrieved successfully')
    except Exception as e:
        logger.exception(f"Error getting user {user_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve user', 500)


@bp.route('/', methods=['POST'])
@token_required
def create_user() -> Tuple[Response, int]:
    """
    Create a new user
    ---
    post:
      summary: Create a new user
      security:
        - Bearer: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserRequest'
      tags:
        - Users
      responses:
        201:
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "User retrieved successfully"
        400:
          description: Invalid input
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        # Service is created with session injected via constructor
        user_service = container.user_service(db)
        
        data = request.get_json()
        errors = request_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        # API now receives password (plain text), not password_hash
        if 'password' not in data:
            return error_response('Password is required', 400)
        
        # Validate password is not empty
        password = data['password']
        if not password or not isinstance(password, str) or not password.strip():
            return error_response('Password cannot be empty', 400)
        
        user = user_service.create_user(
            username=data['username'],
            password=password,  # Plain text password - will be hashed by service
            full_name=data['full_name'],
            email=data['email'],
            status=data.get('status', 'active')
        )
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='User created successfully', status_code=201)
    except ValueError as e:
        # Validation errors from service layer
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return error_response('Failed to create user', 500)


@bp.route('/<int:user_id>/status', methods=['PUT'])
@token_required
def update_user_status(user_id: int) -> Tuple[Response, int]:
    """
    Update user status
    ---
    put:
      summary: Update user status
      security:
        - Bearer: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
      tags:
        - Users
      responses:
        200:
          description: User status updated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "User status updated successfully"
        400:
          description: Invalid input
        404:
          description: User not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        data = request.get_json()
        errors = update_status_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        user = user_service.update_user_status(user_id, data['status'])
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='User status updated successfully')
    except ValueError as e:
        return not_found_response(str(e))
    except Exception as e:
        logger.exception(f"Error updating user status {user_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to update user status', 500)


@bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id: int) -> Tuple[Response, int]:
    """
    Delete a user by id
    ---
    delete:
      summary: Delete a user by id
      security:
        - Bearer: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the user to delete
      tags:
        - Users
      responses:
        204:
          description: User deleted successfully
        404:
          description: User not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        user_service.delete_user(user_id)
        # 204 No Content - return empty body per HTTP spec
        return '', 204
    except ValueError as e:
        return not_found_response('User not found')
    except Exception as e:
        logger.exception(f"Error deleting user {user_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to delete user', 500)


@bp.route('/<int:user_id>/roles', methods=['POST'])
@token_required
@role_required('ADMIN')
def assign_role(user_id: int) -> Tuple[Response, int]:
    """
    Assign a role to a user
    ---
    post:
      summary: Assign a role to a user (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - role_name
              properties:
                role_name:
                  type: string
                  enum: [ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT]
                  description: Role name to assign
                  example: "LECTURER"
      tags:
        - Users
      responses:
        200:
          description: Role assigned successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "Role assigned successfully"
        400:
          description: Invalid input or role already assigned
        404:
          description: User or role not found
        401:
          description: Unauthorized
        403:
          description: Insufficient permissions (Admin required)
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        data = request.get_json()
        
        if not data or 'role_name' not in data:
            return error_response('role_name is required', 400)
        
        role_name = data['role_name'].upper()
        valid_roles = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']
        if role_name not in valid_roles:
            return error_response(f'Invalid role. Must be one of: {", ".join(valid_roles)}', 400)
        
        user = user_service.assign_role(user_id, role_name)
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='Role assigned successfully')
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error assigning role to user {user_id}: {e}")
        return error_response('Failed to assign role', 500)


@bp.route('/<int:user_id>/roles/<role_name>', methods=['DELETE'])
@token_required
@role_required('ADMIN')
def remove_role(user_id: int, role_name: str) -> Tuple[Response, int]:
    """
    Remove a role from a user
    ---
    delete:
      summary: Remove a role from a user (Admin only)
      security:
        - Bearer: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the user
        - name: role_name
          in: path
          required: true
          schema:
            type: string
            enum: [ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT]
          description: Role name to remove
      tags:
        - Users
      responses:
        200:
          description: Role removed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/UserResponse'
                  message:
                    type: string
                    example: "Role removed successfully"
        404:
          description: User or role not found
        401:
          description: Unauthorized
        403:
          description: Insufficient permissions (Admin required)
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        role_name = role_name.upper()
        valid_roles = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']
        if role_name not in valid_roles:
            return error_response(f'Invalid role. Must be one of: {", ".join(valid_roles)}', 400)
        
        user = user_service.remove_role(user_id, role_name)
        user_data = response_schema.dump(user)
        return success_response(data=user_data, message='Role removed successfully')
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error removing role from user {user_id}: {e}")
        return error_response('Failed to remove role', 500)

