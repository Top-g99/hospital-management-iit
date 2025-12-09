from typing import List, Dict, Optional, Tuple, Any
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import User, Role, Appointment, AppointmentStatus, Treatment
from app.extensions import db
from datetime import date, timedelta
from functools import wraps

physician_blueprint = Blueprint('doctor', __name__, url_prefix='/doctor')


def require_physician_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != Role.DOCTOR:
            flash('Access denied. Doctor only.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper


def _get_todays_appointments(physician_id: int) -> List[Appointment]:
    current_date = date.today()
    return Appointment.query.filter(
        Appointment.doctor_id == physician_id,
        Appointment.date == current_date,
        Appointment.status == AppointmentStatus.BOOKED
    ).order_by(Appointment.time).all()


def _get_weekly_appointments(physician_id: int) -> List[Appointment]:
    current_date = date.today()
    week_end = current_date + timedelta(days=7)
    return Appointment.query.filter(
        Appointment.doctor_id == physician_id,
        Appointment.date >= current_date,
        Appointment.date <= week_end,
        Appointment.status == AppointmentStatus.BOOKED
    ).order_by(Appointment.date, Appointment.time).all()


def _get_assigned_patients(physician_id: int, limit: int = 10) -> List[User]:
    all_appointments = Appointment.query.filter_by(doctor_id=physician_id).all()
    patient_ids = {apt.patient_id for apt in all_appointments}
    return User.query.filter(User.id.in_(patient_ids), User.role == Role.PATIENT).limit(limit).all()


def _calculate_dashboard_statistics(today_appts: List[Appointment], week_appts: List[Appointment], patient_count: int) -> Dict[str, int]:
    return {
        'today_appointments': len(today_appts),
        'week_appointments': len(week_appts),
        'total_patients': patient_count
    }


@physician_blueprint.route('/dashboard')
@login_required
@require_physician_access
def display_physician_dashboard() -> Response:
    today_appointments = _get_todays_appointments(current_user.id)
    week_appointments = _get_weekly_appointments(current_user.id)
    assigned_patients = _get_assigned_patients(current_user.id)
    patient_count = len({apt.patient_id for apt in Appointment.query.filter_by(doctor_id=current_user.id).all()})
    
    statistics = _calculate_dashboard_statistics(today_appointments, week_appointments, patient_count)
    
    return render_template('doctor/dashboard.html',
                         stats=statistics,
                         today_appointments=today_appointments,
                         week_appointments=week_appointments,
                         assigned_patients=assigned_patients)


def _build_appointment_query(physician_id: int, status_filter: str):
    query = Appointment.query.filter(Appointment.doctor_id == physician_id)
    if status_filter != 'all':
        query = query.filter(Appointment.status == AppointmentStatus[status_filter.upper()])
    return query.order_by(Appointment.date.desc(), Appointment.time.desc())


@physician_blueprint.route('/appointments')
@login_required
@require_physician_access
def list_physician_appointments() -> Response:
    status_filter = request.args.get('status', 'all')
    appointments = _build_appointment_query(current_user.id, status_filter).all()
    return render_template('doctor/appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter)


def _verify_appointment_ownership(appointment: Appointment, physician_id: int) -> bool:
    return appointment.doctor_id == physician_id


@physician_blueprint.route('/appointments/<int:id>')
@login_required
@require_physician_access
def view_appointment_details(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment is not assigned to you.', 'error')
        return redirect(url_for('doctor.list_physician_appointments'))
    
    return render_template('doctor/view_appointment.html', appointment=appointment)


def _extract_treatment_data() -> Dict[str, str]:
    return {
        'visit_type': request.form.get('visit_type', 'In-person').strip(),
        'tests_done': request.form.get('tests_done', '').strip(),
        'diagnosis': request.form.get('diagnosis', '').strip(),
        'prescription': request.form.get('prescription', '').strip(),
        'medicines': request.form.get('medicines', '').strip(),
        'notes': request.form.get('notes', '').strip()
    }


def _create_or_update_treatment_record(appointment_id: int, treatment_data: Dict[str, str]) -> Treatment:
    treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    if not treatment:
        treatment = Treatment(appointment_id=appointment_id)
        db.session.add(treatment)
    
    treatment.visit_type = treatment_data.get('visit_type', 'In-person')
    treatment.tests_done = treatment_data.get('tests_done', '')
    treatment.diagnosis = treatment_data['diagnosis']
    treatment.prescription = treatment_data.get('prescription', '')
    treatment.medicines = treatment_data.get('medicines', '')
    treatment.notes = treatment_data.get('notes', '')
    return treatment


@physician_blueprint.route('/appointments/<int:id>/complete', methods=['GET', 'POST'])
@login_required
@require_physician_access
def mark_appointment_completed(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment is not assigned to you.', 'error')
        return redirect(url_for('doctor.list_physician_appointments'))
    
    if appointment.status != AppointmentStatus.BOOKED:
        flash('This appointment is already completed or cancelled.', 'error')
        return redirect(url_for('doctor.view_appointment_details', id=id))
    
    if request.method == 'POST':
        treatment_data = _extract_treatment_data()
        
        if not treatment_data['diagnosis']:
            flash('Diagnosis is required.', 'error')
            return render_template('doctor/complete_appointment.html', appointment=appointment)
        
        can_transition, reason = appointment.can_transition_to(AppointmentStatus.COMPLETED)
        if not can_transition:
            flash(f'Cannot complete appointment: {reason}', 'error')
            return render_template('doctor/complete_appointment.html', appointment=appointment)
        
        appointment.status = AppointmentStatus.COMPLETED
        _create_or_update_treatment_record(appointment.id, treatment_data)
        db.session.commit()
        
        flash('Appointment marked as completed and treatment record saved!', 'success')
        return redirect(url_for('doctor.view_appointment_details', id=id))
    
    return render_template('doctor/complete_appointment.html', appointment=appointment)


@physician_blueprint.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
@require_physician_access
def cancel_physician_appointment(id: int) -> Response:
    appointment = Appointment.query.get_or_404(id)
    
    if not _verify_appointment_ownership(appointment, current_user.id):
        flash('Access denied. This appointment is not assigned to you.', 'error')
        return redirect(url_for('doctor.list_physician_appointments'))
    
    if appointment.status != AppointmentStatus.BOOKED:
        flash('Only booked appointments can be cancelled.', 'error')
        return redirect(url_for('doctor.view_appointment_details', id=id))
    
    can_transition, reason = appointment.can_transition_to(AppointmentStatus.CANCELLED)
    if not can_transition:
        flash(f'Cannot cancel appointment: {reason}', 'error')
        return redirect(url_for('doctor.view_appointment_details', id=id))
    
    appointment.status = AppointmentStatus.CANCELLED
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('doctor.view_appointment_details', id=id))


@physician_blueprint.route('/patients')
@login_required
@require_physician_access
def list_assigned_patients() -> Response:
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
    patient_ids = {apt.patient_id for apt in appointments}
    patients = User.query.filter(User.id.in_(patient_ids), User.role == Role.PATIENT).all()
    return render_template('doctor/patients.html', patients=patients)


def _verify_patient_relationship(patient_id: int, physician_id: int) -> bool:
    return Appointment.query.filter_by(
        doctor_id=physician_id,
        patient_id=patient_id
    ).first() is not None


def _get_patient_appointment_history(patient_id: int, physician_id: int) -> Tuple[List[Appointment], List[Appointment], List[Treatment]]:
    appointments = Appointment.query.filter(
        Appointment.doctor_id == physician_id,
        Appointment.patient_id == patient_id
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    completed_appointments = Appointment.query.filter(
        Appointment.doctor_id == physician_id,
        Appointment.patient_id == patient_id,
        Appointment.status == AppointmentStatus.COMPLETED
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.doctor_id == physician_id,
        Appointment.patient_id == patient_id
    ).order_by(Treatment.created_at.desc()).all()
    
    return (appointments, completed_appointments, treatments)


def _calculate_patient_statistics(appointments: List[Appointment], completed: List[Appointment], treatments: List[Treatment]) -> Dict[str, Any]:
    return {
        'total_visits': len(appointments),
        'completed_visits': len(completed),
        'total_treatments': len(treatments),
        'first_visit': appointments[-1].date if appointments else None,
        'last_visit': appointments[0].date if appointments else None,
    }


@physician_blueprint.route('/patients/<int:patient_id>')
@login_required
@require_physician_access
def view_patient_history(patient_id: int) -> Response:
    patient = User.query.get_or_404(patient_id)
    
    if patient.role != Role.PATIENT:
        flash('Invalid patient.', 'error')
        return redirect(url_for('doctor.list_assigned_patients'))
    
    if not _verify_patient_relationship(patient_id, current_user.id):
        flash('This patient has no appointment history with you.', 'warning')
        return redirect(url_for('doctor.list_assigned_patients'))
    
    appointments, completed_appointments, treatments = _get_patient_appointment_history(patient_id, current_user.id)
    statistics = _calculate_patient_statistics(appointments, completed_appointments, treatments)
    
    return render_template('doctor/view_patient.html', 
                         patient=patient, 
                         appointments=appointments,
                         completed_appointments=completed_appointments,
                         treatments=treatments,
                         stats=statistics)


def _extract_availability_from_form() -> Dict[str, List[str]]:
    availability_data = {}
    current_date = date.today()
    
    # Define time slots for morning and evening ranges
    morning_slots = ['08:00', '09:00', '10:00', '11:00', '12:00']
    evening_slots = ['16:00', '17:00', '18:00', '19:00', '20:00', '21:00']
    
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_string = target_date.strftime('%Y-%m-%d')
        selected_slots = request.form.getlist(f'slots_{date_string}')
        
        # Convert slot ranges to individual time slots
        time_slots = []
        if '08:00-12:00' in selected_slots:
            time_slots.extend(morning_slots)
        if '16:00-21:00' in selected_slots:
            time_slots.extend(evening_slots)
        
        availability_data[date_string] = sorted(time_slots) if time_slots else []
    return availability_data


def _build_availability_date_list() -> List[Dict[str, Any]]:
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


@physician_blueprint.route('/availability')
@login_required
@require_physician_access
def manage_availability() -> Response:
    if not current_user.physician_profile:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('doctor.display_physician_dashboard'))
    
    if request.method == 'POST':
        availability_data = _extract_availability_from_form()
        current_user.physician_profile.availability = availability_data
        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('doctor.manage_availability'))
    
    availability_data = current_user.physician_profile.availability or {}
    date_list = _build_availability_date_list()
    
    return render_template('doctor/availability.html', 
                         availability=availability_data,
                         date_list=date_list)


doctor_bp = physician_blueprint
