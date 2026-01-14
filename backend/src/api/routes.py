from api.controllers.user_controller import bp as user_bp
from api.controllers.auth_controller import auth_bp
from api.controllers.syllabus_controller import bp as syllabus_bp
from api.controllers.file_controller import bp as file_bp
from api.controllers.subject_controller import bp as subject_bp
from api.controllers.program_controller import bp as program_bp
from api.controllers.admin_controller import bp as admin_bp
from api.controllers.public_controller import bp as public_bp

def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(syllabus_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(program_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp) 