# Hospital Management System

A comprehensive web-based Hospital Management System built with Flask that manages appointments, patient records, doctor schedules, and medical treatments. The system supports three distinct user roles: Admin, Doctor, and Patient, each with specific functionalities and access levels.

## 🏥 Features

### Admin Features
- **Dashboard**: Comprehensive overview of hospital operations
- **User Management**: Add, edit, and manage doctors and patients
- **Appointment Management**: View and manage all appointments across the system
- **Doctor Management**: Add new doctors, assign specializations, and manage profiles
- **Patient Management**: View patient records, edit profiles, and search functionality
- **Department Management**: Create and manage medical departments
- **Search Functionality**: Search for doctors and patients across the system
- **Appointment Calendar**: View and manage doctor availability schedules

### Doctor Features
- **Doctor Dashboard**: Overview of appointments and patient information
- **Appointment Management**: View and manage assigned appointments
- **Availability Management**: Set and update availability schedules
- **Patient Records**: View patient history and medical records
- **Appointment Completion**: Complete appointments and add treatment records
- **Treatment Documentation**: Record diagnosis, prescriptions, and medical notes

### Patient Features
- **Patient Dashboard**: Personal dashboard with appointment information
- **Book Appointments**: Search for doctors and book appointments
- **View Appointments**: Check upcoming and past appointments
- **Reschedule Appointments**: Modify existing appointment schedules
- **View Medical History**: Access completed appointment records and treatment history
- **Doctor Profiles**: Browse doctor information, specializations, and availability
- **Department Browsing**: Explore different medical departments

## 🛠️ Technology Stack

- **Backend Framework**: Flask 3.0.0
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: Flask-Login 0.6.3
- **Forms**: Flask-WTF 1.2.1, WTForms 3.1.1
- **Security**: Passlib 1.7.4 for password hashing
- **Environment Management**: python-dotenv 1.0.0
- **Frontend**: HTML, CSS, JavaScript
- **Template Engine**: Jinja2 (included with Flask)

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Top-g99/hospital-management-iit.git
   cd hospital-management-iit
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///hospital.db
   FLASK_ENV=development
   PORT=5000
   ```

5. **Initialize the database**
   ```bash
   python setup_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```
   
   Or use the shell script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

7. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`

## 👤 Default Login Credentials

After initial setup, you can login with the default admin account:

- **Email**: `admin@hms.com`
- **Password**: `admin123`

⚠️ **Important**: Change the default admin password after first login in production environments!

## 📁 Project Structure

```
hospital-management-iit/
│
├── app/
│   ├── __init__.py          # Application factory and initialization
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions initialization
│   ├── models.py            # Database models
│   ├── seed.py              # Database seeding utilities
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py         # Admin routes and views
│   │   ├── auth.py          # Authentication routes
│   │   ├── doctor.py        # Doctor routes and views
│   │   └── patient.py       # Patient routes and views
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── login.css
│   │   │   └── style.css
│   │   └── js/
│   │       ├── login.js
│   │       └── main.js
│   │
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   ├── login.html
│       │   ├── register.html
│       │   └── profile.html
│       ├── admin/
│       │   ├── dashboard.html
│       │   ├── doctors.html
│       │   ├── patients.html
│       │   ├── appointments.html
│       │   └── ...
│       ├── doctor/
│       │   ├── dashboard.html
│       │   ├── appointments.html
│       │   ├── availability.html
│       │   └── ...
│       └── patient/
│           ├── dashboard.html
│           ├── book_appointment.html
│           ├── appointments.html
│           └── ...
│
├── instance/                # Instance-specific files (database)
├── venv/                   # Virtual environment (not in git)
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
├── run.sh                  # Shell script to run the app
├── setup_db.py             # Database initialization script
└── README.md               # This file
```

## 🗄️ Database Schema

The system uses the following main database models:

- **SystemUser**: User accounts with roles (Admin, Doctor, Patient)
- **MedicalDepartment**: Hospital departments/specializations
- **PhysicianProfile**: Doctor profiles with specializations and availability
- **ClientProfile**: Patient profiles with personal information
- **MedicalAppointment**: Appointment records linking patients and doctors
- **TreatmentRecord**: Treatment records associated with completed appointments

### Key Features:
- Password hashing using Werkzeug
- Role-based access control
- Appointment status management (Booked, Completed, Cancelled)
- Time slot availability validation
- Cascading deletes for data integrity

## 🔐 Security Features

- Password hashing with Werkzeug's security utilities
- Session management with Flask-Login
- Role-based access control
- CSRF protection with Flask-WTF
- Environment variable configuration for sensitive data
- SQL injection protection via SQLAlchemy ORM

## 🎯 Key Functionalities

### Appointment Management
- Book appointments with available doctors
- Check time slot availability in real-time
- Reschedule existing appointments
- Complete appointments and add treatment records
- View appointment history

### Doctor Availability
- Doctors can set their weekly availability schedules
- JSON-based availability storage for flexibility
- Real-time availability checking
- Conflict prevention for appointment booking

### Treatment Records
- Document diagnosis and prescriptions
- Track medical tests and procedures
- Store treatment notes and follow-up information
- Link treatments to specific appointments

## 🧪 Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python run.py
```

### Database Migrations

Currently using SQLAlchemy's `db.create_all()`. For production, consider using Flask-Migrate for proper migration management.

### Adding New Features

1. Update models in `app/models.py`
2. Create routes in appropriate blueprint in `app/routes/`
3. Add templates in `app/templates/`
4. Update static files if needed

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite:///hospital.db` |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `PORT` | Server port | `5000` |

## 🚢 Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production`
- [ ] Use a production-grade database (PostgreSQL recommended)
- [ ] Configure proper error handling and logging
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Change default admin credentials

### Deploying to Cloud Platforms

The application can be deployed to platforms like:
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Platform
- Azure App Service
- DigitalOcean App Platform

Ensure to set environment variables and configure the database accordingly.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**Top-g99**

- GitHub: [@Top-g99](https://github.com/Top-g99)

## 🙏 Acknowledgments

- Flask framework and its ecosystem
- SQLAlchemy for database ORM
- All contributors and users of this project

## 📞 Support

For support, please open an issue in the GitHub repository.

---

**Note**: This is a project developed for educational purposes. For production use in real healthcare environments, ensure compliance with healthcare data regulations (HIPAA, GDPR, etc.) and implement additional security measures.
