from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    DEBUG: bool = os.getenv('DEBUG').lower() == 'true'  # Convierte a booleano
    SECRET_COOKIE: str = os.getenv('SECRET_COOKIE')


class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI: str = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS').lower() == 'true'  # Convierte a booleano
