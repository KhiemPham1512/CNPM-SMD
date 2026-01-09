from api.controllers.user_controller import bp as user_bp
from api.controllers.auth_controller import auth_bp
from api.controllers.syllabus_controller import bp as syllabus_bp

def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(syllabus_bp) 