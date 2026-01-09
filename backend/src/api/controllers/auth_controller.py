import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

import jwt
from flask import Blueprint, Response, current_app, jsonify, request

from api.utils.db import get_db_session
from api.utils.authz import token_required, get_user_id_from_token, get_user_roles
from api.responses import success_response, error_response
from api.schemas.user import UserResponseSchema
from dependency_container import container

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
response_schema = UserResponseSchema()

@auth_bp.route('/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """
    User login endpoint
    ---
    post:
      summary: Authenticate user and return JWT token
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  description: Username
                  example: "admin"
                password:
                  type: string
                  description: Password
                  format: password
                  example: "admin123"
      responses:
        200:
          description: Login successful
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
                      token:
                        type: string
                        description: JWT token for authentication
                        example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  message:
                    type: string
                    example: "Login successful"
        400:
          description: Username and password are required
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: false
                  message:
                    type: string
                    example: "Username and password are required"
        401:
          description: Invalid credentials
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: false
                  message:
                    type: string
                    example: "Invalid credentials"
        500:
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: false
                  message:
                    type: string
                    example: "Internal server error"
    """
    db = get_db_session()
    try:
        user_service = container.user_service(db)
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return error_response('Username and password are required', 400)
        
        user = user_service.authenticate_user(
            username=data['username'],
            password=data['password']
        )
        
        if not user:
            return error_response('Invalid credentials', 401)

        payload = {
            'user_id': user.user_id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=2)
        }
        secret_key = current_app.config.get('SECRET_KEY')
        if not secret_key:
            return error_response('Server configuration error: SECRET_KEY not set', 500)
        
        # Encode token with HS256 algorithm
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        # Ensure token is a string (PyJWT 2.0+ returns string, but be safe)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # Return token in standard response format
        # Swagger UI will automatically add "Bearer " prefix when user pastes raw token
        return success_response(data={'token': token}, message='Login successful')
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        return error_response('Authentication failed', 500)


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user() -> Tuple[Response, int]:
    """
    Get current authenticated user information
    ---
    get:
      summary: Get current authenticated user
      security:
        - Bearer: []
      tags:
        - Authentication
      responses:
        200:
          description: Current user information
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
                      user:
                        $ref: '#/components/schemas/UserResponse'
                      roles:
                        type: array
                        items:
                          type: string
                        example: ["ADMIN", "LECTURER"]
                  message:
                    type: string
                    example: "User retrieved successfully"
        401:
          description: Unauthorized
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: false
                  message:
                    type: string
                    example: "Unauthorized"
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_service = container.user_service(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        # Get user roles
        roles = get_user_roles(user_id, db)
        
        user_data = response_schema.dump(user)
        return success_response(
            data={
                'user': user_data,
                'roles': roles
            },
            message='User retrieved successfully'
        )
    except Exception as e:
        logger.error(f"Error getting current user: {e}", exc_info=True)
        return error_response('Failed to retrieve user information', 500)