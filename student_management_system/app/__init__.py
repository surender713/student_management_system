import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../student_management.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Import and register blueprints
    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.admin_routes import admin
    from app.routes.teacher_routes import teacher
    from app.routes.student_routes import student
    from app.routes.api_routes import api
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(teacher, url_prefix='/teacher')
    app.register_blueprint(student, url_prefix='/student')
    app.register_blueprint(api, url_prefix='/api')
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        from app.utils import create_default_admin
        create_default_admin(app)
    
    return app 