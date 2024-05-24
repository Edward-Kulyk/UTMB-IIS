from flask import Blueprint, jsonify, render_template, request

from services import (
    campaign_list,
    create_campaign,
    create_link,
    delete_link,
    edit_campaign_row,
    get_default_values_service,
    get_options_context,
    update_link,
)

link = Blueprint(
    "options",
    __name__,
)


@link.route("/", methods=["GET", "POST"])
def link_creation():
    context = get_options_context("unique")
    if request.method == "POST":
        error_message, short_url = create_link(request.form)
        context.update(error_message=error_message, short_url=short_url)

    return render_template("index.html", **context)


@link.route("/add_campaign", methods=["GET", "POST"])
def add_campaign():
    if request.method == "POST":
        create_campaign(request.form)

    return render_template("campaign_creation.html")


@link.route("/campaign_name_list", methods=["GET"])
def campaign_name_list():
    return render_template("campaign_name_list.html", campaigns=campaign_list())


@link.route("/link/api/<int:link_id>", methods=["UPDATE"])
def edit_link(link_id: int):
    data: dict = request.json or {}
    return jsonify(update_link(link_id, data))


@link.route("/link/api/<string:short_link_id>", methods=["DELETE"])
def delete_record(short_link_id: str):
    return delete_link(short_link_id)


@link.route("/get_default_values/<string:campaign_name>", methods=["GET"])
def get_default_values(campaign_name: str):
    if not campaign_name:
        return jsonify({"status": "failure", "message": "Campaign name is required"}), 400

    default_values = get_default_values_service(campaign_name)

    if not default_values:
        return jsonify({"status": "failure", "message": "Campaign not found"}), 404

    return jsonify(default_values)


@link.route("/edit-campaign-row/<int:campaign_id>", methods=["POST"])
def edit_row(campaign_id: int):
    data = request.json
    if data is None:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    success, message = edit_campaign_row(campaign_id, data)
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), 404
