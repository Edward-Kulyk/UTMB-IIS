from flask import Blueprint, redirect

from database import get_db
from services import update_bloggers_avg
from services.ga_service import analytics_data
from utils.short_link import update_clicks_count

main = Blueprint(
    "main",
    __name__,
)

db = get_db()


@main.route("/update-clicks", methods=["GET"])
def update_clicks():
    # update_clicks_count()
    # analytics_data()
    update_bloggers_avg()
    return redirect("/campaigns")
