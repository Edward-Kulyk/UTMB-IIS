from config import Config
from flask import Flask

from src.controllers.campaign_controller import campaign_bp
from src.controllers.options_controller import option_bp
from src.controllers.statistic_controller import statistics_bp
from src.database import models
from src.database.db import engine


def create_app() -> Flask:
    from src.controllers.utm_link_controller import link

    app = Flask(__name__)
    models.Base.metadata.create_all(bind=engine)
    app.config.from_object(Config)
    app.register_blueprint(link, name="link_blueprint")
    app.register_blueprint(option_bp, name="option")
    app.register_blueprint(campaign_bp, name="campaign_blueprint")
    app.register_blueprint(statistics_bp, name="statistics_blueprint")
    return app
