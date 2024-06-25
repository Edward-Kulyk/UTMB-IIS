import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///default.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SHORT_IO_API_KEY = os.getenv("SHORT_IO_API_KEY", "default_secret_key")
    PROPERTY_IDS = [int(id.strip()) for id in os.getenv('PROPERTY_IDS', '').split(',')]
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "default_secret_key")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "default_secret_key")
    DEBUG = False
