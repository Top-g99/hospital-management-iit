# Hospital Management System

A Flask-based web application for managing hospital operations including appointments, patient records, doctor schedules, and treatments. The system has three user roles: Admin, Doctor, and Patient, each with their own set of features.

## Features

Admins can manage everything - they have a dashboard showing the overall hospital operations, can add and edit doctors and patients, manage appointments across the entire system, handle departments, and search through all records. They also have access to appointment calendars and availability schedules.

Doctors get their own dashboard where they can see their appointments, manage their availability schedules, view patient records, and complete appointments by adding treatment records. They can document diagnoses, prescriptions, and medical notes.

Patients can book appointments with doctors, view their upcoming and past appointments, reschedule if needed, check their medical history, browse doctor profiles and departments, and see available time slots.

## Tech Stack

Built with Flask 3.0.0 on the backend, using SQLite as the database with SQLAlchemy as the ORM. Authentication is handled with Flask-Login, forms with Flask-WTF and WTForms. Passwords are hashed using Passlib. Environment variables are managed with python-dotenv. The frontend is standard HTML, CSS, and JavaScript with Jinja2 templates.

## Getting Started

You'll need Python 3.7 or higher and pip. I'd recommend using a virtual environment.

Clone the repo first:

```bash
git clone https://github.com/Top-g99/hospital-management-iit.git
cd hospital-management-iit
```

Create and activate a virtual environment:

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Set up your environment variables. Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` with your settings:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///hospital.db
FLASK_ENV=development
PORT=5000
```

Initialize the database:

```bash
python setup_db.py
```

Run the application:

```bash
python run.py
```

Or use the shell script:

```bash
chmod +x run.sh
./run.sh
```

Then open your browser and go to `http://127.0.0.1:5000`

## Default Login

After setting up, you can log in with the default admin account:
- Email: `admin@hms.com`
- Password: `admin123`

Make sure to change the default password if you're deploying this anywhere.

## Project Structure

The main application code is in the `app` directory. `__init__.py` handles the Flask app initialization, `config.py` has the configuration classes, `extensions.py` initializes Flask extensions, and `models.py` contains all the database models.

Routes are organized in the `routes` folder - there's one file each for admin, auth, doctor, and patient routes.

Static files (CSS and JavaScript) are in `static`, and all the HTML templates are in `templates` organized by user role.

The database gets created in the `instance` folder when you run setup_db.py.

## Database

The main models are SystemUser (handles all user accounts with roles), MedicalDepartment (hospital departments), PhysicianProfile (doctor info and availability), ClientProfile (patient info), MedicalAppointment (appointments linking patients and doctors), and TreatmentRecord (treatment details for completed appointments).

Passwords are hashed with Werkzeug, access is role-based, appointments can be in Booked/Completed/Cancelled states, and there's validation to prevent double-booking time slots. Deletes cascade properly to maintain data integrity.

## Security

Passwords are hashed before storage. Sessions are managed through Flask-Login. Access control is role-based - each route checks the user's role before allowing access. CSRF protection is enabled with Flask-WTF. Sensitive config goes in environment variables. SQLAlchemy handles queries safely to prevent SQL injection.

## How It Works

Appointments can be booked by checking available time slots, rescheduled later, and marked as completed with treatment records attached. Doctors set their availability schedules which are stored as JSON for flexibility. The system prevents booking conflicts by checking availability in real-time.

Treatment records include diagnosis, prescriptions, test results, and notes, all linked to the specific appointment.

## Development

To run in development mode:

```bash
export FLASK_ENV=development
python run.py
```

The database setup uses SQLAlchemy's `db.create_all()` method. For production you'd want to use Flask-Migrate for proper migrations, but for development this works fine.

When adding features, update the models first, then add routes in the appropriate blueprint file, create templates, and update static files as needed.

## Environment Variables

- `SECRET_KEY`: Flask session secret (defaults to a dev key - change this in production)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `FLASK_ENV`: Set to development or production
- `PORT`: Server port (defaults to 5000)

## Deployment Notes

Before deploying to production:
- Change SECRET_KEY to something strong and random
- Set FLASK_ENV=production
- Switch to a proper database like PostgreSQL instead of SQLite
- Set up proper error handling and logging
- Get HTTPS/SSL certificates
- Configure firewall rules
- Set up database backups
- Change the default admin credentials

This should work on most cloud platforms like Heroku, AWS, GCP, Azure, or DigitalOcean. Just make sure to set your environment variables properly and configure the database connection for whatever platform you're using.

## Contributing

Feel free to submit pull requests if you want to contribute. Fork the repo, create a branch, make your changes, and open a PR.

## License

This project is open source under the MIT License.

## Author

Top-g99 - https://github.com/Top-g99

---

Note: This was built as an educational project. If you're planning to use this in a real healthcare setting, you'll need to ensure compliance with healthcare regulations like HIPAA or GDPR and add more security measures accordingly.
