"""
Authorization utility for role-based access control.
Minimal implementation for MVP workflow endpoints.
"""
import logging
from functools import wraps
from typing import List, Optional

import jwt
from flask import current_app, jsonify, request
from sqlalchemy.orm import Session

from api.utils.db import get_db_session
from api.responses import error_response
from domain.services.auth_service import AuthService

logger = logging.getLogger(__name__)


def _extract_token_from_header(auth_header: str) -> str:
    """
    Extract and validate raw JWT token from Authorization header.
    
    Handles cases:
    - "Bearer <token>"
    - "Bearer Bearer <token>" (if user pasted "Bearer <token>" in Swagger)
    - "<token>" (raw token)
    - Headers with extra quotes or whitespace
    
    Returns:
        Raw token string without any "Bearer " prefix, or None if invalid
        
    Raises:
        ValueError: If token format is invalid (not a valid JWT structure)
    """
    if not auth_header:
        return None
    
    # Strip whitespace and quotes
    token = auth_header.strip().strip('"').strip("'")
    
    if not token:
        return None
    
    # Case-insensitive check and strip "Bearer " prefix (handle multiple prefixes)
    # Use while loop to handle "Bearer Bearer <token>" cases
    while token and len(token) >= 7 and token[:7].lower() == 'bearer ':
        token = token[7:].strip().strip('"').strip("'")  # Remove "Bearer " and clean again
    
    if not token:
        return None
    
    # Validate JWT format: must have exactly 3 segments separated by dots
    # JWT format: header.payload.signature (3 parts)
    segments = token.split('.')
    if len(segments) != 3:
        # Log but don't expose token content
        logger.warning(f"Invalid JWT format: expected 3 segments, got {len(segments)}. Token length: {len(token)}")
        if len(token) < 20:
            raise ValueError("Malformed JWT: Token appears incomplete. Please copy the full token from login response.")
        raise ValueError("Malformed JWT (expected 3 segments separated by dots)")
    
    # Basic validation: each segment should not be empty
    if not all(segment.strip() for segment in segments):
        logger.warning("Invalid JWT format: empty segments detected")
        raise ValueError("Malformed JWT (empty segments)")
    
    return token


def token_required(f):
    """
    Decorator to require JWT token authentication.
    Must be used before @role_required decorator.
    
    Usage:
        @bp.route('/endpoint')
        @token_required
        @role_required('HOD', 'ADMIN')
        def my_endpoint():
            ...
    
    Sets request.current_user_id from JWT token.
    Returns 401 if token is missing or invalid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip token validation for OPTIONS requests (CORS preflight)
        # Flask-CORS handles these automatically
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        token = None
        
        # Debug: Log all headers in DEBUG mode
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Request to {request.path} - Headers: {dict(request.headers)}")
        
        # Extract Authorization header (Flask/Werkzeug headers are case-insensitive)
        # Use .get() to safely retrieve header value
        auth_header = request.headers.get("Authorization")
        
        # Defensive: Also check lowercase if needed (though Flask headers are case-insensitive)
        if not auth_header:
            auth_header = request.headers.get("authorization")
        
        if not auth_header:
            logger.warning(f"Missing Authorization header for request to {request.path}")
            return error_response('Missing Authorization header', 401)
        
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Authorization header received: '{auth_header[:50]}...' (length: {len(auth_header)})")
        
        # Extract and validate token from header
        token = None
        try:
            token = _extract_token_from_header(auth_header)
            if current_app.config.get('DEBUG', False):
                logger.debug(f"Extracted token: '{token[:50] if token else None}...' (length: {len(token) if token else 0})")
        except ValueError as e:
            # JWT format validation failed
            logger.warning(f"Invalid JWT format for request to {request.path}: {str(e)}")
            return error_response(str(e), 401)
        
        if not token:
            logger.warning(f"Missing token for request to {request.path}. "
                         f"Authorization header present: True, value: '{auth_header[:100]}...'")
            return error_response('Missing token', 401)
        
        # Get secret key from Flask config
        secret_key = current_app.config.get('SECRET_KEY')
        if not secret_key:
            logger.error("SECRET_KEY not set in app config")
            return error_response('Server configuration error: SECRET_KEY not set', 500)
        
        # Debug logging
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Attempting to verify token with SECRET_KEY length: {len(secret_key)}")
            logger.debug(f"Token first 50 chars: {token[:50]}...")
        
        # Use AuthService to verify token (Clean Architecture)
        try:
            auth_service = AuthService(secret_key=secret_key, algorithm='HS256')
            data = auth_service.verify_token(token)
            
            if current_app.config.get('DEBUG', False):
                logger.debug(f"Token verified successfully. Payload: {data}")
            
            # Attach user info to request context
            request.current_user_id = data['user_id']
            
        except ValueError as e:
            # Token validation error (missing user_id, etc.)
            logger.warning(f"Token validation error for request to {request.path}: {str(e)}")
            return error_response(str(e), 401)
        except jwt.ExpiredSignatureError:
            # Token has expired
            logger.warning(f"Token expired for request to {request.path}")
            return error_response('Token expired', 401)
        except jwt.InvalidSignatureError:
            # Token signature is invalid (wrong secret key)
            logger.warning(f"Invalid token signature for request to {request.path}")
            return error_response('Invalid token signature', 401)
        except jwt.DecodeError:
            # Token cannot be decoded (malformed JWT structure)
            logger.warning(f"Token decode error for request to {request.path}")
            return error_response('Invalid token', 401)
        except jwt.InvalidTokenError:
            # Other invalid token errors (catch-all for PyJWT exceptions)
            logger.warning(f"Invalid token error for request to {request.path}")
            return error_response('Invalid token', 401)
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected token validation error for request to {request.path}: {str(e)}", exc_info=True)
            error_msg = f'Token validation error: {str(e)}' if current_app.config.get('DEBUG', False) else 'Token validation error'
            return error_response(error_msg, 401)
        
        return f(*args, **kwargs)
    return decorated


def get_user_id_from_token() -> Optional[int]:
    """
    Extract user_id from JWT token in request.
    Assumes token_required decorator has already set request.current_user_id.
    """
    if hasattr(request, 'current_user_id'):
        return request.current_user_id
    return None


def get_user_roles(user_id: int, session: Session = None) -> List[str]:
    """
    Fetch user roles using UserService.
    Returns list of role names (e.g., ['LECTURER', 'HOD']).
    
    Args:
        user_id: User ID to get roles for
        session: Optional database session. If not provided, uses Flask g session.
    
    Returns:
        List of role names for the user. Empty list if user has no roles.
    
    Raises:
        ValueError: If user_id is invalid or database operation fails.
        Exception: Any other error from UserService or repository.
    """
    if not user_id:
        return []
    
    # Use provided session or get from Flask g (request context)
    db = session if session is not None else get_db_session()
    
    try:
        from dependency_container import container
        user_service = container.user_service(db)
        return user_service.get_user_roles(user_id)
    except Exception as e:
        logger.error(f"Failed to get user roles for user_id={user_id}: {str(e)}", exc_info=True)
        # Re-raise exception instead of silently returning empty list
        raise


def has_role(user_id: int, required_roles: List[str], session: Session = None) -> bool:
    """
    Check if user has at least one of the required roles.
    
    Args:
        user_id: User ID
        required_roles: List of role names (e.g., ['HOD', 'ADMIN'])
        session: Optional database session. If not provided, creates a new one.
    
    Returns:
        True if user has at least one required role, False otherwise.
        Returns False if user_id is None or required_roles is empty.
    
    Raises:
        Exception: Propagates any exception from get_user_roles (database errors, etc.)
    """
    if not user_id or not required_roles:
        return False
    
    # get_user_roles will raise exception on error, not return empty list silently
    user_roles = get_user_roles(user_id, session)
    return any(role in user_roles for role in required_roles)


def role_required(*allowed_roles: str):
    """
    Decorator to require specific role(s) for an endpoint.
    Must be used after @token_required decorator.
    
    Usage:
        @bp.route('/endpoint')
        @token_required
        @role_required('HOD', 'ADMIN')
        def my_endpoint():
            ...
    
    Returns:
        - 401 if user not authenticated
        - 403 if user lacks required role (expected case)
        - 500 if server error occurs (database failure, etc.)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = get_user_id_from_token()
            if not user_id:
                return error_response('User not authenticated', 401)
            
            # Use Flask g session (shared with controller) - no need to create new session
            db = get_db_session()
            try:
                # Check if user has required role
                # This will raise exception on server errors, return False if no permission
                has_required_role = has_role(user_id, list(allowed_roles), db)
                
                if not has_required_role:
                    # User lacks required role - this is expected, return 403
                    # In production, use generic message to avoid information disclosure
                    is_debug = current_app.config.get('DEBUG', False)
                    if is_debug:
                        # Development: show detailed message
                        error_msg = f'Insufficient permissions. Required roles: {", ".join(allowed_roles)}'
                    else:
                        # Production: generic message
                        error_msg = 'Access denied. You do not have permission to perform this action.'
                    return error_response(error_msg, 403)
                
                # User has required role - set roles on request for potential use in endpoint
                request.current_user_roles = get_user_roles(user_id, db)
            except Exception as e:
                # Server error occurred (database failure, etc.) - log and return 500
                logger.error(
                    f"Error checking role for user_id={user_id}, allowed_roles={allowed_roles}: {str(e)}",
                    exc_info=True
                )
                return error_response('Internal server error while checking permissions', 500)
            # No finally/close needed - Flask teardown handles it
            
            return f(*args, **kwargs)
        return decorated
    return decorator

