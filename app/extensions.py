from typing import TYPE_CHECKING
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

if TYPE_CHECKING:
    pass

# Flask extension instances initialized here for use across the application
# These are initialized separately to avoid circular import issues

database_instance: SQLAlchemy = SQLAlchemy()
authentication_manager: LoginManager = LoginManager()

# Maintain backward compatibility with existing imports
db = database_instance
login_manager = authentication_manager
