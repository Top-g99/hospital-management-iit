# Hospital Management System

A web-based hospital management system built with Flask that helps manage hospital operations including patient appointments, doctor schedules, and medical records.

The system has three types of users:

**Admin** - Manages the entire hospital system. Can add and edit doctors and patients, view all appointments, manage departments, and search through records. Has full access to appointment calendars and availability schedules.

**Doctor** - Can view their appointments, set availability schedules, access patient records and medical history, complete appointments, and document treatments including diagnosis, prescriptions, and medical notes.

**Patient** - Can search for doctors by department or specialization, book appointments, view upcoming and past appointments, reschedule appointments, and access their medical history and treatment records.

The application uses SQLite for data storage and includes features like appointment conflict prevention, role-based access control, password hashing, and treatment record management. Each user role has its own dashboard and interface tailored to their needs.
