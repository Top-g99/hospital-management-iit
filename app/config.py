from typing import Dict, Type, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class ApplicationConfiguration:
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL', 'sqlite:///hospital.db')


class DevelopmentSettings(ApplicationConfiguration):
    DEBUG: bool = True
    FLASK_ENV: str = 'development'
    TEMPLATES_AUTO_RELOAD: bool = True


class ProductionSettings(ApplicationConfiguration):
    DEBUG: bool = False
    FLASK_ENV: str = 'production'


def get_configuration_mapping() -> Dict[str, Type[ApplicationConfiguration]]:
    return {
        'development': DevelopmentSettings,
        'production': ProductionSettings,
        'default': DevelopmentSettings
    }


config = get_configuration_mapping()
