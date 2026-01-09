# Standard library imports
import logging
import os
from inspect import getdoc

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

# Load environment variables from .env file if it exists
load_dotenv()

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
    
    # Load configuration based on environment
    config_class = get_config()
    app.config.from_object(config_class)
    logger.info(f"Loaded configuration: {config_class.__name__}")
    
    # Initialize CORS - must be before registering routes
    init_cors(app)
    
    # Register all route blueprints via routes.py
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

    # Initialize database - fail fast if it fails
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

    # Register routes for Swagger documentation with enhanced schemas
    # APISpec's FlaskPlugin automatically parses YAML docstrings from view functions
    # The docstrings in controllers already include requestBody and response schemas
    registered_paths = []
    failed_paths = []
    
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            # Add endpoints to Swagger spec
            if rule.endpoint.startswith(('user.', 'auth.', 'syllabus.')):
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