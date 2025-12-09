from typing import Optional, Tuple, List, Dict, Any
from datetime import date, time, datetime
from enum import Enum

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa


class UserRole(Enum):
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    PATIENT = 'patient'


class AppointmentState(Enum):
    BOOKED = 'Booked'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'


class SystemUser(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(255), nullable=False)
    role: UserRole = db.Column(db.Enum(UserRole), nullable=False)
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)
    contact: Optional[str] = db.Column(db.String(20))
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    physician_profile = db.relationship('PhysicianProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    client_profile = db.relationship('ClientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    patient_appointments = db.relationship('MedicalAppointment', foreign_keys='MedicalAppointment.patient_id', backref='patient', lazy='dynamic')
    physician_appointments = db.relationship('MedicalAppointment', foreign_keys='MedicalAppointment.doctor_id', backref='doctor', lazy='dynamic')
    
    def encrypt_and_store_password(self, plaintext_password: str) -> None:
        # hash password before storing in db
        if plaintext_password is None:
            raise ValueError("Password cannot be None")
        cleaned_password = plaintext_password.strip()
        if len(cleaned_password) == 0:
            raise ValueError("Password cannot be empty")
        hashed_value = generate_password_hash(cleaned_password)
        self.password_hash = hashed_value
    
    def verify_password(self, plaintext_password: str) -> bool:
        if plaintext_password is None or len(plaintext_password.strip()) == 0:
            return False
        if not hasattr(self, 'password_hash') or self.password_hash is None:
            return False
        stored_hash = self.password_hash
        return check_password_hash(stored_hash, plaintext_password)
    
    set_password = encrypt_and_store_password
    check_password = verify_password
    
    def __repr__(self) -> str:
        return f'<SystemUser {self.email}>'


User = SystemUser
Role = UserRole


class MedicalDepartment(db.Model):
    __tablename__ = 'departments'
    
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    description: Optional[str] = db.Column(db.Text)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    physicians = db.relationship('PhysicianProfile', backref='department', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<MedicalDepartment {self.name}>'


Department = MedicalDepartment


class PhysicianProfile(db.Model):
    __tablename__ = 'doctor_profiles'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    specialization_id: int = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    experience_years: Optional[int] = db.Column(db.Integer, default=0)
    availability: Dict[str, List[str]] = db.Column(db.JSON, default=dict)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<PhysicianProfile {self.user_id}>'


DoctorProfile = PhysicianProfile


class ClientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    dob: Optional[date] = db.Column(db.Date)
    gender: Optional[str] = db.Column(db.String(10))
    address: Optional[str] = db.Column(db.Text)
    contact: Optional[str] = db.Column(db.String(20))
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<ClientProfile {self.user_id}>'


PatientProfile = ClientProfile


class MedicalAppointment(db.Model):
    __tablename__ = 'appointments'
    
    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    doctor_id: int = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date: date = db.Column(db.Date, nullable=False, index=True)
    time: time = db.Column(db.Time, nullable=False, index=True)
    status: AppointmentState = db.Column(db.Enum(AppointmentState), default=AppointmentState.BOOKED, nullable=False)
    notes: Optional[str] = db.Column(db.Text)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    treatment_record = db.relationship('TreatmentRecord', backref='appointment', uselist=False, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_appointment_datetime', 'date', 'time'),
        db.Index('idx_doctor_datetime', 'doctor_id', 'date', 'time'),
        db.UniqueConstraint('doctor_id', 'date', 'time', name='uq_doctor_date_time_booked_slot'),
    )
    
    @staticmethod
    def check_time_slot_availability(physician_id: int, appointment_date: date, appointment_time: time, exclude_appointment_id: Optional[int] = None) -> bool:
        query = MedicalAppointment.query.filter(
            MedicalAppointment.doctor_id == physician_id,
            MedicalAppointment.date == appointment_date,
            MedicalAppointment.time == appointment_time,
            MedicalAppointment.status == AppointmentState.BOOKED
        )
        
        if exclude_appointment_id is not None:
            query = query.filter(MedicalAppointment.id != exclude_appointment_id)
        
        conflicting_appointment = query.first()
        return conflicting_appointment is None
    
    def validate_status_transition(self, target_status: AppointmentState) -> Tuple[bool, Optional[str]]:
        current_status = self.status
        
        if current_status == target_status:
            return (True, None)
        
        if current_status == AppointmentState.BOOKED:
            if target_status in [AppointmentState.COMPLETED, AppointmentState.CANCELLED]:
                return (True, None)
            else:
                return (False, f"Invalid transition from {current_status.value} to {target_status.value}")
        
        if current_status in [AppointmentState.COMPLETED, AppointmentState.CANCELLED]:
            if target_status == AppointmentState.BOOKED:
                return (False, f"Cannot change {current_status.value} appointment back to Booked")
            return (True, None)
        
        return (True, None)
    
    def change_status(self, new_status: AppointmentState, bypass_validation: bool = False) -> Tuple[bool, str]:
        if not bypass_validation:
            is_valid, error_message = self.validate_status_transition(new_status)
            if not is_valid:
                return (False, error_message or "Invalid status transition")
        
        previous_status = self.status
        self.status = new_status
        return (True, f"Status changed from {previous_status.value} to {new_status.value}")
    
    can_transition_to = validate_status_transition
    update_status = change_status
    
    @staticmethod
    def is_slot_available(doctor_id: int, appointment_date: date, appointment_time: time, exclude_id: Optional[int] = None) -> bool:
        return MedicalAppointment.check_time_slot_availability(doctor_id, appointment_date, appointment_time, exclude_id)
    
    @staticmethod
    def get_completed_appointments_for_patient(patient_id: int) -> List['MedicalAppointment']:
        return MedicalAppointment.retrieve_completed_appointments_by_patient(patient_id)
    
    @staticmethod
    def retrieve_completed_appointments_by_patient(patient_identifier: int) -> List['MedicalAppointment']:
        return MedicalAppointment.query.filter(
            MedicalAppointment.patient_id == patient_identifier,
            MedicalAppointment.status == AppointmentState.COMPLETED
        ).order_by(MedicalAppointment.date.desc(), MedicalAppointment.time.desc()).all()
    
    def represents_permanent_record(self) -> bool:
        return self.status == AppointmentState.COMPLETED
    
    def __repr__(self) -> str:
        return f'<MedicalAppointment {self.id} - {self.date} {self.time}>'


Appointment = MedicalAppointment
AppointmentStatus = AppointmentState


class TreatmentRecord(db.Model):
    __tablename__ = 'treatments'
    
    id: int = db.Column(db.Integer, primary_key=True)
    appointment_id: int = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'), unique=True, nullable=False)
    visit_type: Optional[str] = db.Column(db.String(50), default='In-person')
    tests_done: Optional[str] = db.Column(db.Text)
    diagnosis: str = db.Column(db.Text, nullable=False)
    prescription: Optional[str] = db.Column(db.Text)
    medicines: Optional[str] = db.Column(db.Text)
    notes: Optional[str] = db.Column(db.Text)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<TreatmentRecord {self.id} for Appointment {self.appointment_id}>'


Treatment = TreatmentRecord
