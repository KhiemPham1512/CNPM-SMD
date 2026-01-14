from flask_cors import CORS


def init_cors(app):
    """
    Initialize CORS for the Flask app.
    Uses CORS_ORIGINS from app config (set in Config class).
    Flask-CORS automatically handles OPTIONS preflight requests.
    """
    cors_origins = app.config.get('CORS_ORIGINS', ['*'])
    cors_headers = app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization', 'X-Requested-With'])
    
    # Enable CORS for all routes
    # Flask-CORS automatically handles OPTIONS preflight requests
    CORS(app, 
         resources={r"/*": {
             "origins": cors_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": cors_headers,
             "expose_headers": ["Content-Type"],
             "supports_credentials": False,  # Set to False for JWT tokens
             "max_age": 3600  # Cache preflight for 1 hour
         }})
    return app