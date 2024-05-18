from apscheduler.schedulers.base import STATE_RUNNING
from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from config import Config


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)
    app.secret_key = "Mega_secret_key_popici"
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        from routes.main_routes import main as main_routes

        app.register_blueprint(main_routes)
        db.create_all()

        def scheduled_task():
            with app.app_context():
                from utils.short_link import update_clicks_count

                update_clicks_count()
                print("Was updated")

        # Проверяем, запущен ли уже планировщик
        if scheduler.state != STATE_RUNNING:
            scheduler.init_app(app)
            scheduler.add_job(id="Scheduled Task", func=scheduled_task, trigger="interval", hours=4)
            scheduler.start()

    return app
