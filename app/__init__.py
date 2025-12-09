from typing import Optional
from flask import Flask, redirect, url_for
from flask_login import current_user
import os

from app.config import config
from app.extensions import db, login_manager
from app.models import User, Role


class ApplicationBuilder:
    def __init__(self):
        self.app_instance = None
        self.environment = 'development'
    
    def resolve_environment(self, provided: Optional[str] = None) -> str:
        if provided:
            cleaned = provided.strip().lower()
            if cleaned:
                return cleaned
        
        env_from_os = os.environ.get('FLASK_ENV', '').strip().lower()
        if env_from_os:
            return env_from_os
        
        return 'development'
    
    def apply_configuration(self, flask_app: Flask, env_name: str) -> None:
        config_class = config.get(env_name)
        if config_class is None:
            config_class = config.get('default')
        flask_app.config.from_object(config_class)
    
    def configure_authentication(self, flask_app: Flask) -> None:
        login_manager.init_app(flask_app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user_session(user_id_string: str):
            if not user_id_string:
                return None
            
            try:
                user_id_int = int(user_id_string.strip())
                if user_id_int < 1:
                    return None
                
                user_record = User.query.filter_by(id=user_id_int).first()
                if user_record and user_record.is_active:
                    return user_record
                return None
            except (ValueError, TypeError, AttributeError):
                return None
    
    def register_blueprints(self, flask_app: Flask) -> None:
        from app.routes.auth import auth_bp
        from app.routes.admin import admin_bp
        from app.routes.doctor import doctor_bp
        from app.routes.patient import patient_bp
        
        blueprints_to_register = [auth_bp, admin_bp, doctor_bp, patient_bp]
        
        for bp in blueprints_to_register:
            if bp:
                flask_app.register_blueprint(bp)
    
    def setup_database(self, flask_app: Flask) -> None:
        import setup_db
        setup_db.create_database()
        
        with flask_app.app_context():
            db.create_all()
    
    def seed_initial_data(self, flask_app: Flask) -> None:
        with flask_app.app_context():
            try:
                admin_exists = User.query.filter_by(role=Role.ADMIN).first()
                if admin_exists is None:
                    from app.seed import seed_data
                    seed_data(flask_app)
            except Exception as e:
                print(f"Database seeding skipped: {e}")
    
    def setup_root_route(self, flask_app: Flask) -> None:
        @flask_app.route('/')
        def index():
            if not current_user.is_authenticated:
                return redirect(url_for('auth.handle_login_request'))
            
            role = current_user.role
            if role == Role.ADMIN:
                return redirect(url_for('admin.display_admin_dashboard'))
            elif role == Role.DOCTOR:
                return redirect(url_for('doctor.display_physician_dashboard'))
            elif role == Role.PATIENT:
                return redirect(url_for('patient.display_client_dashboard'))
            
            return redirect(url_for('auth.handle_login_request'))
    
    def build(self, env_override: Optional[str] = None) -> Flask:
        self.app_instance = Flask(__name__)
        self.environment = self.resolve_environment(env_override)
        
        self.apply_configuration(self.app_instance, self.environment)
        
        db.init_app(self.app_instance)
        self.configure_authentication(self.app_instance)
        self.register_blueprints(self.app_instance)
        
        self.setup_database(self.app_instance)
        self.seed_initial_data(self.app_instance)
        self.setup_root_route(self.app_instance)
        
        return self.app_instance


def initialize_flask_application(environment_mode: Optional[str] = None) -> Flask:
    builder = ApplicationBuilder()
    return builder.build(environment_mode)


create_app = initialize_flask_application
