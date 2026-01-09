# Configuration settings for the Flask application

import os
import warnings


class Config:
    """Base configuration. Validation happens in get_config() function, not at class definition."""
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1']
    TESTING = os.environ.get('TESTING', 'False').lower() in ['true', '1']
    # DATABASE_URI must be set via environment variable - no hard-coded credentials
    DATABASE_URI = os.environ.get('DATABASE_URI')
    CORS_HEADERS = 'Content-Type'
    
    # CORS configuration - will be overridden by child classes
    CORS_ORIGINS = ['*']  # Default, should be overridden in production
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    
    @staticmethod
    def _validate_secret_key():
        """Validate SECRET_KEY. Called by get_config(), not at class definition."""
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            # Only allow default in development/testing
            flask_env = os.environ.get('FLASK_ENV', '').lower()
            app_env = os.environ.get('APP_ENV', flask_env).lower()
            if app_env in ['development', 'dev', 'test']:
                secret_key = 'dev-secret-key-change-in-production'
                warnings.warn(
                    "Using default SECRET_KEY. This is insecure for production. "
                    "Set SECRET_KEY environment variable.",
                    UserWarning
                )
            else:
                raise ValueError(
                    "SECRET_KEY must be set via environment variable. "
                    "Set SECRET_KEY in your .env file or environment variables."
                )
        return secret_key


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # DATABASE_URI must be set via environment variable - no hard-coded credentials
    # For local development, set DATABASE_URI in .env file
    DATABASE_URI = os.environ.get('DATABASE_URI')
    # Allow all origins in development
    CORS_ORIGINS = ['http://localhost:9999', 'http://127.0.0.1:9999', 'http://localhost:3000', 'http://127.0.0.1:3000']
    
    @staticmethod
    def _validate_database_uri():
        """Development: DATABASE_URI is required but provides helpful warning if missing."""
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            warnings.warn(
                "DATABASE_URI not set in development. Set DATABASE_URI in your .env file. "
                "App will fail to start if DATABASE_URI is not set.",
                UserWarning
            )
            # Return None - app will fail with clear error in init_mssql()
            return None
        return database_uri
    
    @staticmethod
    def _validate_secret_key():
        """Development: allow default SECRET_KEY with warning."""
        return Config._validate_secret_key()


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # DATABASE_URI must be set via environment variable - no hard-coded credentials
    DATABASE_URI = os.environ.get('DATABASE_URI')
    CORS_ORIGINS = ['*']  # Allow all in testing
    
    @staticmethod
    def _validate_database_uri():
        """Testing: DATABASE_URI is required."""
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            raise ValueError("DATABASE_URI must be set in testing environment")
        return database_uri
    
    @staticmethod
    def _validate_secret_key():
        """Testing: allow default SECRET_KEY."""
        return Config._validate_secret_key()


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    @staticmethod
    def _validate_secret_key():
        """Production: SECRET_KEY is mandatory."""
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError(
                "SECRET_KEY must be set in production environment. "
                "Set SECRET_KEY in your .env file or environment variables."
            )
        return secret_key
    
    @staticmethod
    def _validate_database_uri():
        """Production: DATABASE_URI is mandatory."""
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            raise ValueError("DATABASE_URI must be set in production environment")
        return database_uri
    
    @staticmethod
    def _validate_cors_origins():
        """Production: CORS_ORIGINS is mandatory."""
        cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
        cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
        if not cors_origins:
            raise ValueError(
                "CORS_ORIGINS must be set in production environment. "
                "Set CORS_ORIGINS as comma-separated list of allowed origins."
            )
        return cors_origins


def get_config():
    """
    Factory function to get appropriate config class based on environment.
    Validation happens here, not at class definition time.
    """
    # Check APP_ENV first, then FLASK_ENV
    app_env = os.environ.get('APP_ENV', '').lower()
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    env = app_env or flask_env
    
    if env in ['production', 'prod']:
        config_class = ProductionConfig
    elif env in ['testing', 'test']:
        config_class = TestingConfig
    else:
        # Default to development
        config_class = DevelopmentConfig
    
    # Validate and set SECRET_KEY
    config_class.SECRET_KEY = config_class._validate_secret_key()
    
    # Validate DATABASE_URI for all environments
    if hasattr(config_class, '_validate_database_uri'):
        database_uri = config_class._validate_database_uri()
        if database_uri is not None:
            config_class.DATABASE_URI = database_uri
    
    # Production-specific validations
    if config_class == ProductionConfig:
        # DATABASE_URI already validated above
        config_class.CORS_ORIGINS = config_class._validate_cors_origins()
    
    return config_class


# NOTE: SwaggerConfig class below is NOT USED - we use OpenAPI 3.0 via APISpec in api/swagger.py
# This class is kept for reference but should not be imported or used
# The app uses flask-swagger-ui with OpenAPI 3.0 specification from /swagger.json
# class SwaggerConfig:
#     """Swagger configuration - NOT USED (using OpenAPI 3.0 instead)."""
#     template = {
#         "swagger": "2.0",
#         "info": {
#             "title": "SMD API",
#             "description": "Syllabus Management System API",
#             "version": "1.0.0"
#         },
#         "basePath": "/",
#         "schemes": [
#             "http",
#             "https"
#         ],
#         "consumes": [
#             "application/json"
#         ],
#         "produces": [
#             "application/json"
#         ]
#     }
#
#     swagger_config = {
#         "headers": [],
#         "specs": [
#             {
#                 "endpoint": 'apispec',
#                 "route": '/apispec.json',
#                 "rule_filter": lambda rule: True,
#                 "model_filter": lambda tag: True,
#             }
#         ],
#         "static_url_path": "/flasgger_static",
#         "swagger_ui": True,
#         "specs_route": "/docs"
#     }