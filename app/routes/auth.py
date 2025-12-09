from typing import Optional, Tuple, Dict
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Role
from app.extensions import db

authentication_blueprint = Blueprint('auth', __name__, url_prefix='/auth')


class LoginProcessor:
    def collect_form_data(self) -> Dict[str, str]:
        form_fields = ['email', 'password', 'remember']
        collected = {}
        for field in form_fields:
            raw_value = request.form.get(field, '')
            collected[field] = raw_value.strip() if isinstance(raw_value, str) else ''
        return collected
    
    def perform_validation(self, form_data: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        email_value = form_data.get('email', '')
        password_value = form_data.get('password', '')
        
        validation_passed = True
        error_reason = None
        
        if not email_value:
            validation_passed = False
            error_reason = 'Email is required.'
        elif not password_value:
            validation_passed = False
            error_reason = 'Password is required.'
        elif '@' not in email_value:
            validation_passed = False
            error_reason = 'Invalid email format.'
        
        return (validation_passed, error_reason)
    
    def locate_user_account(self, email_input: str) -> Optional[User]:
        processed_email = email_input.strip().lower()
        matching_user = User.query.filter_by(email=processed_email).first()
        return matching_user
    
    def verify_credentials(self, user_instance: Optional[User], provided_password: str) -> bool:
        if user_instance is None:
            return False
        
        password_correct = user_instance.check_password(provided_password)
        account_enabled = getattr(user_instance, 'is_active', False)
        
        return password_correct and account_enabled
    
    def determine_destination(self, user_role: Role) -> str:
        role_destinations = {
            Role.ADMIN: 'admin.display_admin_dashboard',
            Role.DOCTOR: 'doctor.display_physician_dashboard',
            Role.PATIENT: 'patient.display_client_dashboard'
        }
        return role_destinations.get(user_role, 'auth.handle_login_request')


@authentication_blueprint.route('/login', methods=['GET', 'POST'])
def handle_login_request() -> Response:
    processor = LoginProcessor()
    
    if request.method != 'POST':
        return render_template('auth/login.html')
    
    form_data = processor.collect_form_data()
    is_valid, error_msg = processor.perform_validation(form_data)
    
    if not is_valid:
        flash(error_msg or 'Please fill in all fields.', 'error')
        return render_template('auth/login.html')
    
    user_account = processor.locate_user_account(form_data['email'])
    credentials_valid = processor.verify_credentials(user_account, form_data['password'])
    
    if not credentials_valid:
        flash('Invalid email or password.', 'error')
        return render_template('auth/login.html')
    
    remember_setting = form_data.get('remember') == 'on'
    login_user(user_account, remember=remember_setting)
    
    welcome_message = f'Welcome back, {user_account.name}!'
    flash(welcome_message, 'success')
    
    destination = processor.determine_destination(user_account.role)
    return redirect(url_for(destination))


class RegistrationProcessor:
    def __init__(self):
        self.required_fields = ['username', 'password']
    
    def gather_registration_fields(self) -> Dict[str, str]:
        collected_data = {}
        for field_name in self.required_fields:
            raw_value = request.form.get(field_name, '')
            collected_data[field_name] = raw_value.strip() if raw_value else ''
        return collected_data
    
    def validate_all_fields(self, field_data: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        username = field_data.get('username', '').strip()
        password = field_data.get('password', '')
        
        if not username:
            return (False, 'Username is required.')
        
        if not password:
            return (False, 'Password is required.')
        
        if len(password) < 6:
            return (False, 'Password must be at least 6 characters long.')
        
        return (True, None)
    
    def check_username_uniqueness(self, username: str) -> bool:
        normalized = username.strip().lower()
        # Check if username already exists as email
        existing = User.query.filter_by(email=normalized).first()
        return existing is None
    
    def build_user_account(self, field_data: Dict[str, str]) -> User:
        from app.models import PatientProfile
        from datetime import date
        
        username = field_data['username'].strip()
        
        # Use username as both name and email (can be updated later in profile)
        user_instance = User(
            name=username,
            email=username.lower(),  # Use username as email for login
            role=Role.PATIENT,
            contact=None,  # Can be added later
            is_active=True
        )
        user_instance.set_password(field_data['password'])
        db.session.add(user_instance)
        db.session.flush()
        
        # Create patient profile with default values (can be updated later)
        profile_instance = PatientProfile(
            user_id=user_instance.id,
            dob=None,  # Can be added later
            gender='',  # Can be added later
            address='',  # Can be added later
            contact=None  # Can be added later
        )
        db.session.add(profile_instance)
        db.session.commit()
        
        return user_instance


@authentication_blueprint.route('/register', methods=['GET', 'POST'])
def handle_registration_request() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method != 'POST':
        return render_template('auth/register.html')
    
    processor = RegistrationProcessor()
    field_data = processor.gather_registration_fields()
    
    is_valid, error_msg = processor.validate_all_fields(field_data)
    if not is_valid:
        flash(error_msg, 'error')
        return render_template('auth/register.html')
    
    username_available = processor.check_username_uniqueness(field_data['username'])
    if not username_available:
        flash('Username already taken. Please choose another or login instead.', 'error')
        return redirect(url_for('auth.handle_login_request'))
    
    processor.build_user_account(field_data)
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.handle_login_request'))


@authentication_blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def handle_logout_request() -> Response:
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.handle_login_request'))


@authentication_blueprint.route('/profile')
@login_required
def display_user_profile() -> Response:
    return render_template('auth/profile.html', user=current_user)


auth_bp = authentication_blueprint
