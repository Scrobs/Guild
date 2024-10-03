# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
import os
import redis

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'  # Redirects to login page if not authenticated

# Configure Redis connection (if using Flask-Limiter with Redis)
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.Redis.from_url(redis_url)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url
)

csrf = CSRFProtect() 
