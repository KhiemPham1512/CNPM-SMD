from flask_cors import CORS


def init_cors(app):
    """
    Initialize CORS for the Flask app.
    Uses CORS_ORIGINS from app config (set in Config class).
    """
    cors_origins = app.config.get('CORS_ORIGINS', ['*'])
    cors_headers = app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization', 'X-Requested-With'])
    
    CORS(app, 
         resources={r"/*": {
             "origins": cors_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": cors_headers,
             "expose_headers": ["Content-Type"]
         }})
    return app