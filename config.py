# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')  # Use a strong secret key in production
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///board_game_club.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    # Flask-Limiter configuration
    RATELIMIT_HEADERS_ENABLED = True
