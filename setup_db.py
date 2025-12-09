from typing import Optional
import sqlite3
import os
from werkzeug.security import generate_password_hash


def _create_users_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'patient')),
            contact TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


def _create_specializations_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS specializations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


def _create_doctors_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            specialization TEXT,
            availability_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')


def _create_patients_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            age INTEGER,
            gender TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')


def _create_appointments_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status TEXT DEFAULT 'Booked' CHECK(status IN ('Booked', 'Completed', 'Cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')


def _create_treatments_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL UNIQUE,
            diagnosis TEXT NOT NULL,
            prescription TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
        )
    ''')


def _create_database_indexes(cursor: sqlite3.Cursor) -> None:
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
        'CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)',
        'CREATE INDEX IF NOT EXISTS idx_appointments_time ON appointments(time)',
        'CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)'
    ]
    for index_sql in indexes:
        cursor.execute(index_sql)


def _check_admin_exists(cursor: sqlite3.Cursor) -> bool:
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('admin@hms.com',))
    return cursor.fetchone()[0] > 0


def _insert_default_admin(cursor: sqlite3.Cursor) -> None:
    admin_password_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO users (name, email, password, role, contact, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Admin', 'admin@hms.com', admin_password_hash, 'admin', '+1234567890', 'active'))
    print("✓ Default admin user created (admin@hms.com / admin123)")


def initialize_database_schema() -> None:
    db_path = 'hospital.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    _create_users_table(cursor)
    _create_specializations_table(cursor)
    _create_doctors_table(cursor)
    _create_patients_table(cursor)
    _create_appointments_table(cursor)
    _create_treatments_table(cursor)
    _create_database_indexes(cursor)
    
    if not _check_admin_exists(cursor):
        _insert_default_admin(cursor)
    else:
        print("✓ Admin user already exists")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database '{db_path}' created successfully with all tables!")
    print("✓ All tables created programmatically:")
    print("  - users")
    print("  - specializations")
    print("  - doctors")
    print("  - patients")
    print("  - appointments")
    print("  - treatments")


if __name__ == '__main__':
    print("Setting up database...")
    initialize_database_schema()
    print("Database setup completed!")


create_database = initialize_database_schema
