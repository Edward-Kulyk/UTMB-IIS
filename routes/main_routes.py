from flask import Blueprint, redirect

from database import get_session
from services import update_bloggers_avg

main = Blueprint(
    "main",
    __name__,
)

db = get_session()


@main.route("/update-clicks", methods=["GET"])
def update_clicks():
    # update_clicks_count()
    # analytics_data()
    update_bloggers_avg()
    return redirect("/campaigns")
