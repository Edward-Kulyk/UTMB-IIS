from flask import Blueprint, render_template, request, send_file

from config import Config
from services import add_date_stamp_to_image, get_and_save_channel_id, get_bloggers, update_bloggers_avg

other = Blueprint(
    "other_routes",
    __name__,
)


@other.route("/data-stamp", methods=["GET"])
def data_stamp():
    return render_template("data-stamp.html")


@other.route("/add_data_stamp", methods=["POST"])
def add_data_stamp():
    photo = request.files["photo"]
    date_str = request.form["date"]

    try:
        img_bytes = add_date_stamp_to_image(photo.stream, date_str)
    except Exception as e:
        return {"status": "error", "message": e}, 400

    return send_file(img_bytes, mimetype="image/jpeg", as_attachment=True, download_name="modified_image.jpg")


@other.route("/bloggers", methods=["GET", "POST"])
def bloggers_page():
    bloggers = get_bloggers()
    if request.method == "POST":
        name = request.form["social_name"]
        yt_name = request.form.get("yt_name", False)
        if yt_name:
            get_and_save_channel_id(Config.api_key, yt_name, name)
            update_bloggers_avg()

    return render_template("new_observ.html", bloggers=bloggers)
