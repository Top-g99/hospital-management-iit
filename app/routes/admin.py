from typing import Dict, List, Optional, Tuple
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import User, Role, Appointment, Department, DoctorProfile, AppointmentStatus
from app.extensions import db
from datetime import date, timedelta
from sqlalchemy import or_
from functools import wraps

administrator_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


def require_administrator_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role == Role.ADMIN
        if not is_admin:
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper


def _calculate_dashboard_statistics() -> Dict[str, int]:
    doctor_count = User.query.filter_by(role=Role.DOCTOR).count()
    patient_count = User.query.filter_by(role=Role.PATIENT).count()
    appointment_total = Appointment.query.count()
    today_date = date.today()
    upcoming_count = Appointment.query.filter(
        Appointment.status == AppointmentStatus.BOOKED,
        Appointment.date >= today_date
    ).count()
    
    return {
        'total_doctors': doctor_count,
        'total_patients': patient_count,
        'total_appointments': appointment_total,
        'upcoming_appointments': upcoming_count
    }


def _get_recent_appointments(limit: int = 10) -> List[Appointment]:
    return Appointment.query.order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).limit(limit).all()


def _get_upcoming_appointments(limit: int = 10) -> List[Appointment]:
    today_date = date.today()
    return Appointment.query.filter(
        Appointment.status == AppointmentStatus.BOOKED,
        Appointment.date >= today_date
    ).order_by(Appointment.date, Appointment.time).limit(limit).all()


@administrator_blueprint.route('/dashboard')
@login_required
@require_administrator_access
def display_admin_dashboard() -> Response:
    statistics = _calculate_dashboard_statistics()
    recent_appointments = _get_recent_appointments()
    doctors = User.query.filter_by(role=Role.DOCTOR).all()
    patients = User.query.filter_by(role=Role.PATIENT).all()
    upcoming_appointments = _get_upcoming_appointments()
    return render_template('admin/dashboard.html', 
                         stats=statistics, 
                         recent_appointments=recent_appointments,
                         doctors=doctors,
                         patients=patients,
                         upcoming_appointments=upcoming_appointments)


@administrator_blueprint.route('/doctors')
@login_required
@require_administrator_access
def list_all_physicians() -> Response:
    physicians = User.query.filter_by(role=Role.DOCTOR).all()
    return render_template('admin/doctors.html', doctors=physicians)


def _generate_default_availability_schedule() -> Dict[str, List[str]]:
    schedule = {}
    current_date = date.today()
    default_slots = ['09:00', '10:00', '14:00', '15:00']
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_string = target_date.strftime('%Y-%m-%d')
        schedule[date_string] = default_slots.copy()
    return schedule


def _create_physician_account(form_data: Dict[str, str]) -> User:
    physician_user = User(
        name=form_data['name'],
        email=form_data['email'],
        role=Role.DOCTOR,
        contact=form_data.get('contact'),
        is_active=True
    )
    physician_user.set_password(form_data['password'])
    db.session.add(physician_user)
    db.session.flush()
    return physician_user


def _create_physician_profile(user_id: int, specialization_id: int, availability: Dict[str, List[str]], experience_years: int = 0) -> DoctorProfile:
    profile = DoctorProfile(
        user_id=user_id,
        specialization_id=specialization_id,
        experience_years=experience_years,
        availability=availability
    )
    db.session.add(profile)
    return profile


@administrator_blueprint.route('/doctors/add', methods=['GET', 'POST'])
@login_required
@require_administrator_access
def add_new_physician() -> Response:
    if request.method == 'POST':
        form_data = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', '').strip(),
            'contact': request.form.get('contact', '').strip(),
            'specialization_id': request.form.get('specialization_id', '').strip(),
            'experience_years': request.form.get('experience_years', '0').strip()
        }
        
        required_fields = ['name', 'email', 'password', 'specialization_id']
        if not all(form_data.get(field) for field in required_fields):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('admin.add_new_physician'))
        
        if User.query.filter_by(email=form_data['email']).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('admin.add_new_physician'))
        
        try:
            experience_years = int(form_data['experience_years']) if form_data['experience_years'] else 0
        except (ValueError, TypeError):
            experience_years = 0
        
        physician_user = _create_physician_account(form_data)
        availability_schedule = _generate_default_availability_schedule()
        _create_physician_profile(physician_user.id, int(form_data['specialization_id']), availability_schedule, experience_years)
        
        db.session.commit()
        flash(f'Doctor {form_data["name"]} added successfully!', 'success')
        return redirect(url_for('admin.list_all_physicians'))
    
    departments = Department.query.all()
    return render_template('admin/add_doctor.html', departments=departments)


@administrator_blueprint.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@require_administrator_access
def modify_physician_profile(doctor_id: int) -> Response:
    physician = User.query.get_or_404(doctor_id)
    if physician.role != Role.DOCTOR:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('admin.list_all_physicians'))
    
    if request.method == 'POST':
        physician.name = request.form.get('name', '').strip()
        physician.email = request.form.get('email', '').strip()
        physician.contact = request.form.get('contact', '').strip()
        
        new_password = request.form.get('password', '').strip()
        if new_password:
            physician.set_password(new_password)
        
        if physician.physician_profile:
            specialization_id = request.form.get('specialization_id', '').strip()
            if specialization_id:
                physician.physician_profile.specialization_id = int(specialization_id)
        
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.list_all_physicians'))
    
    departments = Department.query.all()
    return render_template('admin/edit_doctor.html', doctor=physician, departments=departments)


@administrator_blueprint.route('/doctors/<int:doctor_id>/delete', methods=['POST'])
@login_required
@require_administrator_access
def remove_physician(doctor_id: int) -> Response:
    physician = User.query.get_or_404(doctor_id)
    if physician.role != Role.DOCTOR:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('admin.list_all_physicians'))
    
    physician_name = physician.name
    db.session.delete(physician)
    db.session.commit()
    flash(f'Doctor {physician_name} deleted successfully!', 'success')
    return redirect(url_for('admin.list_all_physicians'))


@administrator_blueprint.route('/doctors/<int:doctor_id>/blacklist', methods=['POST'])
@login_required
@require_administrator_access
def blacklist_physician(doctor_id: int) -> Response:
    physician = User.query.get_or_404(doctor_id)
    if physician.role != Role.DOCTOR:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('admin.list_all_physicians'))
    
    physician_name = physician.name
    physician.is_active = False
    db.session.commit()
    flash(f'Doctor {physician_name} has been blacklisted.', 'success')
    return redirect(url_for('admin.list_all_physicians'))


def _extract_availability_from_form() -> Dict[str, List[str]]:
    availability_data = {}
    current_date = date.today()
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_string = target_date.strftime('%Y-%m-%d')
        time_slots = request.form.getlist(f'slots_{date_string}')
        availability_data[date_string] = sorted(time_slots) if time_slots else []
    return availability_data


def _build_date_list_for_template() -> List[Dict[str, any]]:
    date_list = []
    current_date = date.today()
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_list.append({
            'date': target_date,
            'date_str': target_date.strftime('%Y-%m-%d'),
            'date_display': target_date.strftime('%A, %B %d, %Y')
        })
    return date_list


@administrator_blueprint.route('/doctors/<int:doctor_id>/availability', methods=['GET', 'POST'])
@login_required
@require_administrator_access
def manage_physician_availability(doctor_id: int) -> Response:
    physician = User.query.get_or_404(doctor_id)
    if physician.role != Role.DOCTOR or not physician.physician_profile:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('admin.list_all_physicians'))
    
    if request.method == 'POST':
        availability_data = _extract_availability_from_form()
        physician.physician_profile.availability = availability_data
        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('admin.list_all_physicians'))
    
    availability_data = physician.physician_profile.availability or {}
    date_list = _build_date_list_for_template()
    
    return render_template('admin/doctor_availability.html', 
                         doctor=physician, 
                         availability=availability_data,
                         date_list=date_list)


def _build_appointment_query(status_filter: str, date_filter: str, view_type: str):
    query = Appointment.query
    
    if status_filter != 'all':
        query = query.filter(Appointment.status == AppointmentStatus[status_filter.upper()])
    
    if date_filter:
        query = query.filter(Appointment.date == date.fromisoformat(date_filter))
    
    current_date = date.today()
    if view_type == 'upcoming':
        query = query.filter(Appointment.date >= current_date)
    elif view_type == 'past':
        query = query.filter(Appointment.date < current_date)
    
    return query.order_by(Appointment.date.desc(), Appointment.time.desc())


def _calculate_appointment_counts() -> Tuple[int, int, int]:
    current_date = date.today()
    upcoming = Appointment.query.filter(Appointment.date >= current_date).count()
    past = Appointment.query.filter(Appointment.date < current_date).count()
    total = Appointment.query.count()
    return (upcoming, past, total)


@administrator_blueprint.route('/appointments')
@login_required
@require_administrator_access
def list_all_appointments() -> Response:
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', '')
    view_type = request.args.get('view', 'all')
    
    appointments = _build_appointment_query(status_filter, date_filter, view_type).all()
    upcoming_count, past_count, all_count = _calculate_appointment_counts()
    
    return render_template('admin/appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         view_type=view_type,
                         upcoming_count=upcoming_count,
                         past_count=past_count,
                         all_count=all_count,
                         today=date.today())


@administrator_blueprint.route('/appointments/<int:appointment_id>')
@login_required
@require_administrator_access
def view_appointment_details(appointment_id: int) -> Response:
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('admin/view_appointment.html', appointment=appointment)


@administrator_blueprint.route('/appointments/<int:appointment_id>/update-status', methods=['POST'])
@login_required
@require_administrator_access
def modify_appointment_status(appointment_id: int) -> Response:
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status_string = request.form.get('status', '').strip()
    
    valid_statuses = ['Booked', 'Completed', 'Cancelled']
    if not new_status_string or new_status_string not in valid_statuses:
        flash('Invalid status selected.', 'error')
        return redirect(url_for('admin.view_appointment', appointment_id=appointment_id))
    
    try:
        new_status = AppointmentStatus[new_status_string.upper()]
        previous_status = appointment.status
        
        can_transition, reason = appointment.can_transition_to(new_status)
        
        if not can_transition:
            flash(f'Status changed from {previous_status.value} to {new_status.value}. Note: {reason}', 'warning')
        else:
            flash(f'Appointment status updated from {previous_status.value} to {new_status.value} successfully!', 'success')
        
        appointment.status = new_status
        db.session.commit()
        
    except (KeyError, ValueError):
        flash('Invalid status value.', 'error')
    
    return redirect(url_for('admin.view_appointment', appointment_id=appointment_id))


@administrator_blueprint.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
@login_required
@require_administrator_access
def remove_appointment(appointment_id: int) -> Response:
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.status == AppointmentStatus.COMPLETED:
        flash('Cannot delete completed appointments. They are permanent medical records.', 'error')
        return redirect(url_for('admin.view_appointment', appointment_id=appointment_id))
    
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted successfully!', 'success')
    return redirect(url_for('admin.list_all_appointments'))


@administrator_blueprint.route('/patients')
@login_required
@require_administrator_access
def list_all_patients() -> Response:
    patients = User.query.filter_by(role=Role.PATIENT).all()
    return render_template('admin/patients.html', patients=patients)


@administrator_blueprint.route('/patients/<int:patient_id>')
@login_required
@require_administrator_access
def view_patient_details(patient_id: int) -> Response:
    patient = User.query.get_or_404(patient_id)
    if patient.role != Role.PATIENT:
        flash('Invalid patient.', 'error')
        return redirect(url_for('admin.list_all_patients'))
    
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.date.desc()
    ).all()
    
    return render_template('admin/view_patient.html', patient=patient, appointments=appointments)


@administrator_blueprint.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@require_administrator_access
def modify_patient_profile(patient_id: int) -> Response:
    patient = User.query.get_or_404(patient_id)
    if patient.role != Role.PATIENT:
        flash('Invalid patient.', 'error')
        return redirect(url_for('admin.list_all_patients'))
    
    if request.method == 'POST':
        patient.name = request.form.get('name', '').strip()
        patient.email = request.form.get('email', '').strip()
        patient.contact = request.form.get('contact', '').strip()
        
        if patient.patient_profile:
            dob_string = request.form.get('dob', '').strip()
            if dob_string:
                patient.patient_profile.dob = date.fromisoformat(dob_string)
            patient.patient_profile.gender = request.form.get('gender', '').strip()
            patient.patient_profile.address = request.form.get('address', '').strip()
        
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.view_patient', patient_id=patient_id))
    
    return render_template('admin/edit_patient.html', patient=patient)


@administrator_blueprint.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
@require_administrator_access
def delete_patient(patient_id: int) -> Response:
    patient = User.query.get_or_404(patient_id)
    if patient.role != Role.PATIENT:
        flash('Invalid patient.', 'error')
        return redirect(url_for('admin.list_all_patients'))
    
    patient_name = patient.name
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient {patient_name} deleted successfully!', 'success')
    return redirect(url_for('admin.list_all_patients'))


@administrator_blueprint.route('/patients/<int:patient_id>/blacklist', methods=['POST'])
@login_required
@require_administrator_access
def deactivate_patient(patient_id: int) -> Response:
    patient = User.query.get_or_404(patient_id)
    if patient.role != Role.PATIENT:
        flash('Invalid patient.', 'error')
        return redirect(url_for('admin.list_all_patients'))
    
    patient_name = patient.name
    patient.is_active = False
    db.session.commit()
    flash(f'Patient {patient_name} has been blacklisted.', 'success')
    return redirect(url_for('admin.list_all_patients'))


def _search_physicians_by_query(search_query: str) -> List[User]:
    return User.query.filter_by(role=Role.DOCTOR).outerjoin(DoctorProfile).outerjoin(Department).filter(
        or_(
            User.name.ilike(f'%{search_query}%'),
            Department.name.ilike(f'%{search_query}%')
        )
    ).distinct().all()


def _search_patients_by_query(search_query: str) -> List[User]:
    filters = [
        User.name.ilike(f'%{search_query}%'),
        User.email.ilike(f'%{search_query}%'),
        User.contact.ilike(f'%{search_query}%')
    ]
    
    try:
        patient_id = int(search_query)
        filters.append(User.id == patient_id)
    except ValueError:
        pass
    
    return User.query.filter_by(role=Role.PATIENT).filter(or_(*filters)).all()


@administrator_blueprint.route('/search')
@login_required
@require_administrator_access
def perform_search() -> Response:
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    results = {
        'doctors': [],
        'patients': [],
        'query': search_query,
        'type': search_type
    }
    
    if search_query:
        if search_type in ['all', 'doctors']:
            results['doctors'] = _search_physicians_by_query(search_query)
        
        if search_type in ['all', 'patients']:
            results['patients'] = _search_patients_by_query(search_query)
    
    return render_template('admin/search.html', results=results)


admin_bp = administrator_blueprint
