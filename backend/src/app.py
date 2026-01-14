# Standard library imports
import logging
import os
from inspect import getdoc
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

# Local application imports
from api.middleware import middleware
from api.routes import register_routes
from api.swagger import spec
from api.utils.db import close_db_session
from config import get_config
from cors import init_cors
from infrastructure.databases import init_db

# Optional YAML validation - if PyYAML is not installed, skip validation
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Load environment variables from .env file
# Priority: backend/.env (project root) > backend/src/.env (fallback)
BASE_DIR = Path(__file__).resolve().parent  # backend/src/
ENV_PATH = BASE_DIR.parent / ".env"  # backend/.env
ENV_PATH_FALLBACK = BASE_DIR / ".env"  # backend/src/.env

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded .env from: {ENV_PATH}")
elif ENV_PATH_FALLBACK.exists():
    load_dotenv(dotenv_path=ENV_PATH_FALLBACK, override=True)
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded .env from: {ENV_PATH_FALLBACK}")
else:
    # Fallback to default load_dotenv() behavior (current directory)
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.warning(f".env file not found at {ENV_PATH} or {ENV_PATH_FALLBACK}. Using default load_dotenv() behavior.")

# Setup logging configuration early
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('DEBUG', 'False').lower() in ['true', '1'] else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

if not HAS_YAML:
    logger.warning("PyYAML not installed - YAML docstring validation will be skipped")


def create_app():
    app = Flask(__name__)
    
    # Disable strict slashes to prevent redirects that break CORS preflight
    # This prevents Flask from redirecting /users to /users/ or vice versa
    app.url_map.strict_slashes = False
    
    # Load configuration based on environment
    config_class = get_config()
    app.config.from_object(config_class)
    logger.info(f"Loaded configuration: {config_class.__name__}")
    
    # Log file storage configuration status (masked for security)
    file_storage_enabled = app.config.get('FILE_STORAGE_ENABLED', False)
    if file_storage_enabled:
        supabase_url = app.config.get('SUPABASE_URL', '')
        supabase_bucket = app.config.get('SUPABASE_BUCKET', 'syllabus-files')
        service_key_present = bool(app.config.get('SUPABASE_SERVICE_ROLE_KEY'))
        # Mask URL (show only domain, not full path)
        masked_url = supabase_url.split('@')[0] + '@***' if '@' in supabase_url else (supabase_url[:20] + '...' if len(supabase_url) > 20 else supabase_url) if supabase_url else 'NOT SET'
        logger.info(
            f"File storage: ENABLED | "
            f"Bucket: {supabase_bucket} | "
            f"Supabase URL: {masked_url} | "
            f"Service key: {'SET' if service_key_present else 'NOT SET'}"
        )
    else:
        logger.info("File storage: DISABLED (set FILE_STORAGE_ENABLED=true to enable)")
    
    # Initialize CORS - must be before registering routes
    init_cors(app)
    
    # Initialize database BEFORE registering routes - fail fast if it fails
    # This ensures DB is ready before any route handlers are registered
    try:
        init_db(app)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        # Re-raise to prevent app from running with broken database
        raise
    
    # Register middleware
    middleware(app)
    
    # Register database session teardown
    app.teardown_appcontext(close_db_session)
    
    # Register all route blueprints via routes.py (AFTER DB init)
    register_routes(app)

    # Swagger UI blueprint - using OpenAPI 3.0
    SWAGGER_URL = '/docs'
    API_URL = '/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "SMD API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Register routes for Swagger documentation with enhanced schemas
    # APISpec's FlaskPlugin automatically parses YAML docstrings from view functions
    # The docstrings in controllers already include requestBody and response schemas
    registered_paths = []
    failed_paths = []
    
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            # Add endpoints to Swagger spec
            if rule.endpoint.startswith(('user.', 'auth.', 'syllabus.', 'file.')):
                view_func = app.view_functions[rule.endpoint]
                doc = getdoc(view_func)
                
                # Validate YAML docstring before parsing
                has_yaml = doc and '---' in doc
                if has_yaml and HAS_YAML:
                    # Try to validate YAML format
                    try:
                        # Extract YAML part after '---'
                        yaml_part = doc.split('---', 1)[1].strip()
                        yaml.safe_load(yaml_part)  # Validate YAML syntax
                    except yaml.YAMLError as yaml_err:
                        logger.warning(f"Invalid YAML docstring for {rule.rule} ({rule.endpoint}): {yaml_err}")
                        failed_paths.append((rule.rule, rule.endpoint, f"Invalid YAML: {yaml_err}"))
                        continue
                    except Exception as e:
                        logger.warning(f"Error validating YAML for {rule.rule} ({rule.endpoint}): {e}", exc_info=True)
                        failed_paths.append((rule.rule, rule.endpoint, f"YAML validation error: {e}"))
                        continue
                
                # Register path with error handling
                try:
                    spec.path(view=view_func)
                    registered_paths.append(rule.rule)
                    if has_yaml:
                        logger.debug(f"Added path: {rule.rule} -> {view_func.__name__} (with YAML docstring)")
                    else:
                        logger.debug(f"Added path: {rule.rule} -> {view_func.__name__} (no YAML docstring)")
                except Exception as e:
                    logger.error(f"[SWAGGER ERROR] endpoint={rule.endpoint} rule={rule.rule} error={e}", exc_info=True)
                    failed_paths.append((rule.rule, rule.endpoint, str(e)))
                    # Continue with other endpoints - don't crash

    # Log summary
    logger.info(f"Swagger registration complete: {len(registered_paths)} paths registered, {len(failed_paths)} failed")
    if failed_paths:
        logger.warning("Failed endpoints:")
        for rule, endpoint, error in failed_paths:
            logger.warning(f"  - {rule} ({endpoint}): {error}")

    @app.route("/swagger.json")
    def swagger_json():
        """Return OpenAPI 3.0 specification"""
        try:
            spec_dict = spec.to_dict()
            return jsonify(spec_dict)
        except Exception as e:
            logger.error(f"Failed to generate swagger.json: {e}", exc_info=True)
            return jsonify({"error": "Failed to generate API specification"}), 500

    return app
# Run the application

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=9999, debug=True)