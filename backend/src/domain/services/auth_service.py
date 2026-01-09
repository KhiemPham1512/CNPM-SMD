"""
Authentication service for JWT token verification.

This service handles JWT token verification without any Flask dependencies,
following Clean Architecture principles.
"""
import logging
from typing import Dict, Optional

import jwt

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service for JWT token verification.
    
    This service is framework-agnostic and contains no Flask imports.
    It handles JWT decoding, expiry checking, and signature validation.
    """
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        """
        Initialize AuthService.
        
        Args:
            secret_key: Secret key used to sign JWT tokens
            algorithm: JWT algorithm (default: HS256)
        """
        if not secret_key:
            raise ValueError("secret_key is required")
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: Raw JWT token string (without "Bearer " prefix)
        
        Returns:
            dict: Decoded token payload containing user information
        
        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidSignatureError: If token signature is invalid
            jwt.DecodeError: If token cannot be decoded (malformed)
            jwt.InvalidTokenError: For other invalid token errors
            ValueError: If token is missing required fields (e.g., user_id)
        """
        if not token:
            raise ValueError("Token is required")
        
        try:
            # Decode token with secret key and algorithm
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Validate required fields
            if 'user_id' not in payload:
                logger.warning(f"Token decoded but missing user_id. Payload keys: {list(payload.keys())}")
                raise ValueError("Token payload missing required field: user_id")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except jwt.InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise
        except jwt.DecodeError:
            logger.warning("Token decode error (malformed JWT)")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected token validation error: {e}", exc_info=True)
            raise ValueError(f"Token validation error: {str(e)}")
