from typing import Dict, List, Optional
from flask import Flask
from app.extensions import db
from app.models import User, Department, DoctorProfile, PatientProfile, Role, Appointment, AppointmentState, Treatment
from datetime import date, timedelta, time, datetime


def _check_if_seeding_required() -> bool:
    existing_admin = User.query.filter_by(role=Role.ADMIN).first()
    return existing_admin is None


def _create_administrator_account() -> User:
    administrator = User(
        name='Hospital Admin',
        email='admin@hms.com',
        role=Role.ADMIN,
        is_active=True,
        contact='+1234567890'
    )
    administrator.set_password('admin123')
    db.session.add(administrator)
    print("✓ Created Admin user (admin@hms.com / admin123)")
    return administrator


def _get_department_definitions() -> List[Dict[str, str]]:
    return [
        {
            'name': 'Cardiology',
            'description': 'Specializes in heart and cardiovascular system diseases and conditions.'
        },
        {
            'name': 'Orthopedics',
            'description': 'Focuses on the diagnosis, treatment, and prevention of disorders of the bones, joints, ligaments, tendons, and muscles.'
        },
        {
            'name': 'Dermatology',
            'description': 'Deals with the diagnosis and treatment of skin, hair, and nail disorders.'
        }
    ]


def _create_medical_departments() -> Dict[str, Department]:
    department_mapping: Dict[str, Department] = {}
    department_definitions = _get_department_definitions()
    
    for dept_info in department_definitions:
        existing_dept = Department.query.filter_by(name=dept_info['name']).first()
        if existing_dept is None:
            new_department = Department(
                name=dept_info['name'],
                description=dept_info['description']
            )
            db.session.add(new_department)
            print(f"✓ Created Department: {dept_info['name']}")
            department_mapping[dept_info['name']] = new_department
        else:
            department_mapping[dept_info['name']] = existing_dept
    
    db.session.flush()
    return department_mapping


def _generate_weekly_availability_schedule() -> Dict[str, List[str]]:
    schedule: Dict[str, List[str]] = {}
    current_date = date.today()
    standard_time_slots = ['09:00', '10:00', '14:00', '15:00']
    
    for day_offset in range(7):
        target_date = current_date + timedelta(days=day_offset)
        date_string = target_date.strftime('%Y-%m-%d')
        schedule[date_string] = standard_time_slots.copy()
    
    return schedule


def _create_sample_physicians(departments: Dict[str, Department]) -> List[User]:
    physicians_data = [
        {
            'name': 'Dr. Emily Chen',
            'email': 'emily@hms.com',
            'password': 'doctor123',
            'department': 'Orthopedics',
            'contact': '+1234567896'
        },
        {
            'name': 'Dr. Emily Chen',
            'email': 'emily@hms.com',
            'password': 'doctor123',
            'department': 'Orthopedics',
            'contact': '+1234567896'
        },
        {
            'name': 'Dr. David Wilson',
            'email': 'david@hms.com',
            'password': 'doctor123',
            'department': 'Dermatology',
            'contact': '+1234567897'
        },
        {
            'name': 'Dr. Lisa Anderson',
            'email': 'lisa@hms.com',
            'password': 'doctor123',
            'department': 'Cardiology',
            'contact': '+1234567898'
        }
    ]
    
    physician_users = []
    for physician_data in physicians_data:
        # Check if doctor already exists
        existing_doctor = User.query.filter_by(email=physician_data['email']).first()
        if existing_doctor:
            physician_users.append(existing_doctor)
            print(f"✓ Doctor already exists: {physician_data['name']} ({physician_data['email']})")
            continue
        
        physician_user = User(
            name=physician_data['name'],
            email=physician_data['email'],
            role=Role.DOCTOR,
            is_active=True,
            contact=physician_data['contact']
        )
        physician_user.set_password(physician_data['password'])
        db.session.add(physician_user)
        db.session.flush()
        
        availability_schedule = _generate_weekly_availability_schedule()
        dept = departments.get(physician_data['department'])
        
        if dept:
            physician_profile = DoctorProfile(
                user_id=physician_user.id,
                specialization_id=dept.id,
                availability=availability_schedule
            )
            db.session.add(physician_profile)
            physician_users.append(physician_user)
            print(f"✓ Created Doctor: {physician_data['name']} ({physician_data['email']} / {physician_data['password']}) - {physician_data['department']}")
    
    return physician_users


def _create_sample_patients() -> List[User]:
    patients_data = [
        {
            'name': 'Jane Doe',
            'email': 'patient@hms.com',
            'password': 'patient123',
            'dob': date(1990, 5, 15),
            'gender': 'Female',
            'address': '123 Main Street, City, State 12345',
            'contact': '+1234567892'
        },
        {
            'name': 'Michael Johnson',
            'email': 'michael@hms.com',
            'password': 'patient123',
            'dob': date(1985, 8, 22),
            'gender': 'Male',
            'address': '456 Oak Avenue, City, State 12346',
            'contact': '+1234567893'
        },
        {
            'name': 'Sarah Williams',
            'email': 'sarah@hms.com',
            'password': 'patient123',
            'dob': date(1992, 3, 10),
            'gender': 'Female',
            'address': '789 Pine Road, City, State 12347',
            'contact': '+1234567894'
        },
        {
            'name': 'Robert Brown',
            'email': 'robert@hms.com',
            'password': 'patient123',
            'dob': date(1978, 11, 5),
            'gender': 'Male',
            'address': '321 Elm Street, City, State 12348',
            'contact': '+1234567895'
        }
    ]
    
    patient_users = []
    for patient_data in patients_data:
        # Check if patient already exists
        existing_patient = User.query.filter_by(email=patient_data['email']).first()
        if existing_patient:
            patient_users.append(existing_patient)
            print(f"✓ Patient already exists: {patient_data['name']} ({patient_data['email']})")
            continue
        
        patient_user = User(
            name=patient_data['name'],
            email=patient_data['email'],
            role=Role.PATIENT,
            is_active=True,
            contact=patient_data['contact']
        )
        patient_user.set_password(patient_data['password'])
        db.session.add(patient_user)
        db.session.flush()
        
        patient_profile = PatientProfile(
            user_id=patient_user.id,
            dob=patient_data['dob'],
            gender=patient_data['gender'],
            address=patient_data['address'],
            contact=patient_data['contact']
        )
        db.session.add(patient_profile)
        patient_users.append(patient_user)
        print(f"✓ Created Patient: {patient_data['name']} ({patient_data['email']} / {patient_data['password']})")
    
    return patient_users


def _create_sample_appointments(doctors: List[User], patients: List[User]) -> None:
    today = date.today()
    appointments_data = [
        {
            'patient': patients[0] if patients else None,
            'doctor': doctors[0] if doctors else None,
            'date': today + timedelta(days=2),
            'time': time(9, 0),
            'status': AppointmentState.BOOKED,
            'notes': 'Regular checkup'
        },
        {
            'patient': patients[0] if patients else None,
            'doctor': doctors[0] if doctors else None,
            'date': today - timedelta(days=5),
            'time': time(10, 0),
            'status': AppointmentState.COMPLETED,
            'notes': 'Follow-up appointment'
        },
        {
            'patient': patients[1] if len(patients) > 1 else None,
            'doctor': doctors[1] if len(doctors) > 1 else None,
            'date': today + timedelta(days=3),
            'time': time(14, 0),
            'status': AppointmentState.BOOKED,
            'notes': 'Initial consultation'
        },
        {
            'patient': patients[1] if len(patients) > 1 else None,
            'doctor': doctors[1] if len(doctors) > 1 else None,
            'date': today - timedelta(days=10),
            'time': time(15, 0),
            'status': AppointmentState.COMPLETED,
            'notes': 'Treatment review'
        },
        {
            'patient': patients[2] if len(patients) > 2 else None,
            'doctor': doctors[2] if len(doctors) > 2 else None,
            'date': today + timedelta(days=1),
            'time': time(9, 0),
            'status': AppointmentState.BOOKED,
            'notes': 'Skin examination'
        },
        {
            'patient': patients[0] if patients else None,
            'doctor': doctors[0] if doctors else None,
            'date': today - timedelta(days=7),
            'time': time(11, 0),
            'status': AppointmentState.CANCELLED,
            'notes': 'Patient requested cancellation'
        }
    ]
    
    created_appointments = []
    for apt_data in appointments_data:
        if not apt_data['patient'] or not apt_data['doctor']:
            continue
        
        appointment = Appointment(
            patient_id=apt_data['patient'].id,
            doctor_id=apt_data['doctor'].id,
            date=apt_data['date'],
            time=apt_data['time'],
            status=apt_data['status'],
            notes=apt_data['notes']
        )
        db.session.add(appointment)
        db.session.flush()
        created_appointments.append((appointment, apt_data['status']))
        print(f"✓ Created {apt_data['status'].value} appointment: {apt_data['patient'].name} with {apt_data['doctor'].name} on {apt_data['date']}")
    
    return created_appointments


def _create_sample_treatments(appointments_with_status: List[tuple]) -> None:
    treatments_data = [
        {
            'diagnosis': 'Hypertension - Stage 1',
            'prescription': 'Lisinopril 10mg once daily, Monitor blood pressure weekly',
            'notes': 'Patient advised to reduce sodium intake and increase physical activity. Follow-up in 3 months.'
        },
        {
            'diagnosis': 'Lower back pain - Musculoskeletal strain',
            'prescription': 'Ibuprofen 400mg three times daily for 5 days, Physical therapy recommended',
            'notes': 'Patient should avoid heavy lifting. Ice pack application for 15 minutes, 3 times daily.'
        },
        {
            'diagnosis': 'Acne vulgaris - Moderate severity',
            'prescription': 'Topical retinoid cream (apply at night), Benzoyl peroxide wash (morning)',
            'notes': 'Patient advised to maintain proper skincare routine. Review in 6 weeks.'
        }
    ]
    
    treatment_index = 0
    for appointment, status in appointments_with_status:
        if status == AppointmentState.COMPLETED and treatment_index < len(treatments_data):
            treatment = Treatment(
                appointment_id=appointment.id,
                diagnosis=treatments_data[treatment_index]['diagnosis'],
                prescription=treatments_data[treatment_index]['prescription'],
                notes=treatments_data[treatment_index]['notes']
            )
            db.session.add(treatment)
            treatment_index += 1
            print(f"✓ Created treatment record for appointment {appointment.id}")


def _display_credentials_summary() -> None:
    print("\n" + "="*50)
    print("Default login credentials:")
    print("="*50)
    print("  Admin:  admin@hms.com / admin123")
    print("\n  Doctors:")
    print("    - doctor@hms.com / doctor123 (Cardiology)")
    print("    - emily@hms.com / doctor123 (Orthopedics)")
    print("    - david@hms.com / doctor123 (Dermatology)")
    print("    - lisa@hms.com / doctor123 (Cardiology)")
    print("\n  Patients:")
    print("    - patient@hms.com / patient123")
    print("    - michael@hms.com / patient123")
    print("    - sarah@hms.com / patient123")
    print("    - robert@hms.com / patient123")
    print("="*50)


def populate_initial_database_records(flask_app: Flask) -> None:
    # seed departments, doctors, patients, appointments and treatments
    with flask_app.app_context():
        # Check if comprehensive sample data already exists
        existing_doctors = User.query.filter_by(role=Role.DOCTOR).count()
        existing_patients = User.query.filter_by(role=Role.PATIENT).count()
        existing_appointments = Appointment.query.count()
        
        # Only skip if we have 4+ doctors, 4+ patients AND appointments exist
        if existing_doctors >= 4 and existing_patients >= 4 and existing_appointments >= 5:
            print("Comprehensive sample data already exists. Skipping seed data.")
            return
        
        print("Seeding database with comprehensive sample data...")
        print("-" * 50)
        
        # Admin is created by setup_db.py, so we skip it here
        department_mapping = _create_medical_departments()
        
        print("\nCreating sample doctors...")
        doctors = _create_sample_physicians(department_mapping)
        
        print("\nCreating sample patients...")
        patients = _create_sample_patients()
        
        print("\nCreating sample appointments...")
        appointments_with_status = _create_sample_appointments(doctors, patients)
        
        print("\nCreating treatment records...")
        _create_sample_treatments(appointments_with_status)
        
        db.session.commit()
        print("\n" + "="*50)
        print("✓ Database seeding completed successfully!")
        print("="*50)
        _display_credentials_summary()


seed_data = populate_initial_database_records
