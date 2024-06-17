from flask import Flask

from config import Config
from database import engine
from models import models
from routes import link, options, other, statistics


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "Secret_key_01231244245457498236598742689756328_dsada"
    app.config.from_object(Config)

    with app.app_context():
        from routes.main_routes import main as main_routes

        app.register_blueprint(main_routes)
        app.register_blueprint(options, name="options_blueprint")
        app.register_blueprint(link, name="link_blueprint")
        app.register_blueprint(statistics, name="statistics_blueprint")
        app.register_blueprint(other)
        models.Base.metadata.create_all(bind=engine)

    return app
