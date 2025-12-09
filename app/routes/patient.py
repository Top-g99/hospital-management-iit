from typing import List, Dict, Optional, Tuple
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import User, Role, Appointment, Department, Treatment, AppointmentStatus, DoctorProfile
from app.extensions import db
from datetime import date, datetime, timedelta
from functools import wraps

client_blueprint = Blueprint('patient', __name__, url_prefix='/patient')


def require_client_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != Role.PATIENT:
            flash('Access denied. Patient only.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper


def _normalize_date_time_inputs(appointment_date: any, appointment_time: any) -> Tuple[date, datetime.time]:
    if isinstance(appointment_date, str):
        appointment_date = date.fromisoformat(appointment_date)
    
    if isinstance(appointment_time, str):
        appointment_time = datetime.strptime(appointment_time, '%H:%M').time()
    
    return (appointment_date, appointment_time)


def verify_slot_availability(doctor_id: int, appointment_date: any, appointment_time: any, exclude_appointment_id: Optional[int] = None) -> Tuple[bool, Optional[Appointment]]:
    normalized_date, normalized_time = _normalize_date_time_inputs(appointment_date, appointment_time)
    
    is_available = Appointment.is_slot_available(
        doctor_id, 
        normalized_date, 
        normalized_time, 
        exclude_id=exclude_appointment_id
    )
    
    existing = None
    if not is_available:
        query = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == normalized_date,
            Appointment.time == normalized_time,
            Appointment.status == AppointmentStatus.BOOKED
        )
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        existing = query.first()
    
    return (not is_available, existing)


def _build_doctor_availability_data(doctors: List[User]) -> List[Dict[str, any]]:
    doctor_availability = []
    current_date = date.today()
    
    for doctor in doctors:
        if doctor.physician_profile and doctor.physician_profile.availability:
            availability_data = {
                'doctor': doctor,
                'availability': {}
            }
            for day_offset in range(7):
                check_date = current_date + timedelta(days=day_offset)
                date_string = check_date.strftime('%Y-%m-%d')
                if date_string in doctor.physician_profile.availability:
                    slots = doctor.physician_profile.availability[date_string]
                    if slots:
                        availability_data['availability'][date_string] = slots
            if availability_data['availability']:
                doctor_availability.append(availability_data)
    
    return doctor_availability


@client_blueprint.route('/dashboard')
@login_required
@require_client_access
def display_client_dashboard() -> Response:
    specializations = Department.query.all()
    doctors = User.query.filter_by(role=Role.DOCTOR, is_active=True).join(DoctorProfile).all()
    doctor_availability = _build_doctor_availability_data(doctors)
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.date >= date.today(),
        Appointment.status == AppointmentStatus.BOOKED
    ).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    recent_treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Treatment.created_at.desc()).limit(5).all()
    
    return render_template('patient/dashboard.html',
                         specializations=specializations,
                         doctor_availability=doctor_availability,
                         upcoming_appointments=upcoming_appointments,
                         recent_treatments=recent_treatments,
                         today=date.today(),
                         timedelta=timedelta)


@client_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
@require_client_access
def update_client_profile() -> Response:
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip()
        current_user.email = request.form.get('email', '').strip()
        current_user.contact = request.form.get('contact', '').strip()
        
        new_password = request.form.get('password', '').strip()
        if new_password:
            current_user.set_password(new_password)
        
        if current_user.patient_profile:
            dob_string = request.form.get('dob', '').strip()
            if dob_string:
                current_user.patient_profile.dob = date.fromisoformat(dob_string)
            current_user.patient_profile.gender = request.form.get('gender', '').strip()
            current_user.patient_profile.address = request.form.get('address', '').strip()
            current_user.patient_profile.contact = request.form.get('contact', '').strip()
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.update_client_profile'))
    
    return render_template('patient/profile.html')


def _build_doctor_search_query(specialization_id: Optional[str], name_query: str):
    query = User.query.filter_by(role=Role.DOCTOR, is_active=True).join(DoctorProfile)
    
    if specialization_id:
        query = query.filter(DoctorProfile.specialization_id == int(specialization_id))
    
    if name_query:
        query = query.filter(User.name.ilike(f'%{name_query}%'))
    
    return query


def _filter_doctors_by_date(doctors: List[User], target_date: date) -> List[Dict[str, any]]:
    available_doctors = []
    date_string = target_date.strftime('%Y-%m-%d')
    
    for doctor in doctors:
        if doctor.physician_profile and doctor.physician_profile.availability:
            if date_string in doctor.physician_profile.availability:
                slots = doctor.physician_profile.availability[date_string]
                if slots:
                    available_doctors.append({
                        'doctor': doctor,
                        'available_slots': slots
                    })
    
    return available_doctors


def _find_next_available_date(doctor: User) -> Optional[date]:
    current_date = date.today()
    for day_offset in range(7):
        check_date = current_date + timedelta(days=day_offset)
        date_string = check_date.strftime('%Y-%m-%d')
        if doctor.physician_profile and doctor.physician_profile.availability:
            if date_string in doctor.physician_profile.availability:
                slots = doctor.physician_profile.availability[date_string]
                if slots:
                    return check_date
    return None


@client_blueprint.route('/department/<int:department_id>')
@login_required
@require_client_access
def view_department(department_id: int) -> Response:
    department = Department.query.get_or_404(department_id)
    doctors = User.query.filter_by(role=Role.DOCTOR, is_active=True).join(DoctorProfile).filter(
        DoctorProfile.specialization_id == department_id
    ).all()
    return render_template('patient/department.html', department=department, doctors=doctors)


@client_blueprint.route('/doctor/<int:doctor_id>')
@login_required
@require_client_access
def view_physician_profile(doctor_id: int) -> Response:
    doctor = User.query.get_or_404(doctor_id)
    if doctor.role != Role.DOCTOR or not doctor.physician_profile:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('patient.display_client_dashboard'))
    return render_template('patient/physician_profile.html', doctor=doctor)


@client_blueprint.route('/doctor/<int:doctor_id>/availability')
@login_required
@require_client_access
def view_doctor_availability(doctor_id: int) -> Response:
    doctor = User.query.get_or_404(doctor_id)
    if doctor.role != Role.DOCTOR or not doctor.physician_profile:
        flash('Invalid doctor.', 'error')
        return redirect(url_for('patient.display_client_dashboard'))
    
    availability = doctor.physician_profile.availability or {}
    current_date = date.today()
    date_list = []
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_list.append({
            'date': target_date,
            'date_str': target_date.strftime('%Y-%m-%d'),
            'date_display': target_date.strftime('%d/%m/%Y')
        })
    
    return render_template('patient/doctor_availability.html', 
                         doctor=doctor, 
                         availability=availability,
                         date_list=date_list)


@client_blueprint.route('/search-doctors')
@login_required
@require_client_access
def search_physicians() -> Response:
    specialization_id = request.args.get('specialization', '')
    date_filter = request.args.get('date', '')
    name_query = request.args.get('name', '').strip()
    
    doctors = _build_doctor_search_query(specialization_id, name_query).all()
    
    available_doctors = []
    if date_filter:
        target_date = date.fromisoformat(date_filter)
        available_doctors = _filter_doctors_by_date(doctors, target_date)
    else:
        for doctor in doctors:
            if doctor.physician_profile and doctor.physician_profile.availability:
                next_available = _find_next_available_date(doctor)
                available_doctors.append({
                    'doctor': doctor,
                    'next_available': next_available,
                    'availability': doctor.physician_profile.availability
                })
    
    specializations = Department.query.all()
    
    return render_template('patient/search_doctors.html',
                         doctors=available_doctors,
                         specializations=specializations,
                         selected_specialization=specialization_id,
                         selected_date=date_filter,
                         selected_name=name_query,
                         today=date.today(),
                         timedelta=timedelta)


def _validate_doctor_availability(doctor: User, appointment_date: str, appointment_time: str) -> Tuple[bool, Optional[str]]:
    if not doctor.physician_profile or not doctor.physician_profile.availability:
        return (False, 'Doctor is not available on this date.')
    
    if appointment_date not in doctor.physician_profile.availability:
        return (False, 'Doctor is not available on this date.')
    
    available_slots = doctor.physician_profile.availability[appointment_date]
    if appointment_time not in available_slots:
        return (False, 'Selected time slot is not available. Please choose another time.')
    
    return (True, None)


@client_blueprint.route('/book-appointment', methods=['GET', 'POST'])
@login_required
@require_client_access
def create_appointment() -> Response:
    if request.method == 'GET':
        # Handle pre-selected parameters from doctor availability page
        doctor_id = request.args.get('doctor_id', '').strip()
        pre_date = request.args.get('date', '').strip()
        pre_time = request.args.get('time', '').strip()
        
        # If all parameters are provided, create appointment directly
        if doctor_id and pre_date and pre_time:
            doctor = User.query.get(int(doctor_id))
            if doctor and doctor.role == Role.DOCTOR:
                is_valid, error_message = _validate_doctor_availability(doctor, pre_date, pre_time)
                if is_valid:
                    is_conflict, existing = verify_slot_availability(doctor.id, pre_date, pre_time)
                    if not is_conflict:
                        appointment = Appointment(
                            patient_id=current_user.id,
                            doctor_id=doctor.id,
                            date=date.fromisoformat(pre_date),
                            time=datetime.strptime(pre_time, '%H:%M').time(),
                            status=AppointmentStatus.BOOKED,
                            notes=''
                        )
                        db.session.add(appointment)
                        db.session.commit()
                        flash('Appointment booked successfully!', 'success')
                        return redirect(url_for('patient.view_appointment_details', id=appointment.id))
                    else:
                        flash('This time slot is already booked. Please choose another time.', 'error')
                else:
                    flash(error_message, 'error')
        
        # Otherwise, show the booking form
        specialization_id = request.args.get('specialization', '')
        selected_doctor_id = doctor_id if doctor_id else ''
        
        specializations = Department.query.all()
        doctors = []
        
        if specialization_id:
            doctors = User.query.filter_by(role=Role.DOCTOR, is_active=True).join(DoctorProfile).filter(
                DoctorProfile.specialization_id == int(specialization_id)
            ).all()
        elif doctor_id:
            doctor = User.query.get(int(doctor_id))
            if doctor and doctor.role == Role.DOCTOR:
                doctors = [doctor]
        
        return render_template('patient/book_appointment.html',
                             specializations=specializations,
                             doctors=doctors,
                             selected_specialization=specialization_id,
                             selected_doctor_id=selected_doctor_id,
                             pre_date=pre_date,
                             pre_time=pre_time,
                             today=date.today(),
                             timedelta=timedelta)
    
    elif request.method == 'POST':
        doctor_id = request.form.get('doctor_id', '').strip()
        appointment_date = request.form.get('date', '').strip()
        appointment_time = request.form.get('time', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not all([doctor_id, appointment_date, appointment_time]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('patient.create_appointment'))
        
        doctor = User.query.get(int(doctor_id))
        if not doctor or doctor.role != Role.DOCTOR:
            flash('Invalid doctor selected.', 'error')
            return redirect(url_for('patient.create_appointment'))
        
        is_valid, error_message = _validate_doctor_availability(doctor, appointment_date, appointment_time)
        if not is_valid:
            flash(error_message, 'error')
            return redirect(url_for('patient.create_appointment'))
        
        is_conflict, existing = verify_slot_availability(doctor.id, appointment_date, appointment_time)
        if is_conflict:
            flash('This time slot is already booked. Please choose another time.', 'error')
            return redirect(url_for('patient.create_appointment'))
        
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor.id,
            date=date.fromisoformat(appointment_date),
            time=datetime.strptime(appointment_time, '%H:%M').time(),
            status=AppointmentStatus.BOOKED,
            notes=notes
        )
        db.session.add(appointment)
        
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while booking the appointment. Please try again.', 'error')
            return redirect(url_for('patient.create_appointment'))
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.list_client_appointments'))


def _build_client_appointment_query(client_id: int, status_filter: str):
    query = Appointment.query.filter(Appointment.patient_id == client_id)
    if status_filter != 'all':
        query = query.filter(Appointment.status == AppointmentStatus[status_filter.upper()])
    return query.order_by(Appointment.date.desc(), Appointment.time.desc())


@client_blueprint.route('/appointments')
@login_required
@require_client_access
def list_client_appointments() -> Response:
    status_filter = request.args.get('status', 'all')
    appointments = _build_client_appointment_query(current_user.id, status_filter).all()
    return render_template('patient/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter)


def _verify_appointment_ownership(appointment: Appointment, client_id: int) -> bool:
    return appointment.patient_id == client_id


@client_blueprint.route('/appointments/<int:id>')
@login_required
@require_client_access
def view_appointment_details(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment does not belong to you.', 'error')
        return redirect(url_for('patient.list_client_appointments'))
    
    return render_template('patient/view_appointment.html', appointment=appointment)


@client_blueprint.route('/appointments/<int:id>/reschedule', methods=['GET', 'POST'])
@login_required
@require_client_access
def reschedule_client_appointment(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment does not belong to you.', 'error')
        return redirect(url_for('patient.list_client_appointments'))
    
    if appointment.status != AppointmentStatus.BOOKED:
        flash('Only booked appointments can be rescheduled.', 'error')
        return redirect(url_for('patient.view_appointment_details', id=id))
    
    if request.method == 'POST':
        new_date = request.form.get('date', '').strip()
        new_time = request.form.get('time', '').strip()
        
        if not all([new_date, new_time]):
            flash('Please select both date and time.', 'error')
            return render_template('patient/reschedule_appointment.html', 
                                 appointment=appointment,
                                 today=date.today(),
                                 timedelta=timedelta)
        
        doctor = appointment.doctor
        is_valid, error_message = _validate_doctor_availability(doctor, new_date, new_time)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('patient/reschedule_appointment.html', 
                                 appointment=appointment,
                                 today=date.today(),
                                 timedelta=timedelta)
        
        is_conflict, existing = verify_slot_availability(
            appointment.doctor_id,
            new_date,
            new_time,
            exclude_appointment_id=appointment.id
        )
        
        if is_conflict:
            flash('This time slot is already booked. Please choose another time.', 'error')
            return render_template('patient/reschedule_appointment.html', 
                                 appointment=appointment,
                                 today=date.today(),
                                 timedelta=timedelta)
        
        appointment.date = date.fromisoformat(new_date)
        appointment.time = datetime.strptime(new_time, '%H:%M').time()
        db.session.commit()
        
        flash('Appointment rescheduled successfully!', 'success')
        return redirect(url_for('patient.view_appointment_details', id=id))
    
    return render_template('patient/reschedule_appointment.html', 
                         appointment=appointment,
                         today=date.today(),
                         timedelta=timedelta)


@client_blueprint.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
@require_client_access
def cancel_client_appointment(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment does not belong to you.', 'error')
        return redirect(url_for('patient.list_client_appointments'))
    
    if appointment.status != AppointmentStatus.BOOKED:
        flash('Only booked appointments can be cancelled.', 'error')
        return redirect(url_for('patient.view_appointment_details', id=id))
    
    can_transition, reason = appointment.can_transition_to(AppointmentStatus.CANCELLED)
    if not can_transition:
        flash(f'Cannot cancel appointment: {reason}', 'error')
        return redirect(url_for('patient.view_appointment_details', id=id))
    
    appointment.status = AppointmentStatus.CANCELLED
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('patient.list_client_appointments'))


@client_blueprint.route('/history')
@login_required
@require_client_access
def view_treatment_history() -> Response:
    appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    completed_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status == AppointmentStatus.COMPLETED
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Treatment.created_at.desc()).all()
    
    return render_template('patient/history.html',
                         appointments=appointments,
                         completed_appointments=completed_appointments,
                         treatments=treatments)


patient_bp = client_blueprint
