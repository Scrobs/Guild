# app/__init__.py

import os
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import atexit
import logging
from logging.handlers import RotatingFileHandler
from .extensions import db, migrate, login, limiter, csrf
from .bgg import update_all_games

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Setup Logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/board_game_club.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Board Game Club startup')
    else:
        # Setup debug logging
        logging.basicConfig(level=logging.DEBUG)

    # Setup Scheduler
    scheduler = BackgroundScheduler()

    def scheduled_job():
        app.logger.info("Scheduled job started: Updating all games.")
        update_all_games(app)
        app.logger.info("Scheduled job completed: All games updated.")

    scheduler.add_job(func=scheduled_job, trigger="interval", hours=24)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Register user_loader callback for Flask-Login
    @login.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    return app
