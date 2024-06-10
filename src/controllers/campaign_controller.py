from flask import Blueprint, jsonify, render_template, request

from src.services.campaign_service import campaign_list, get_default_for_campaign, edit_campaign_row

campaign_bp = Blueprint(
    "campaign",
    __name__,
)


@campaign_bp.route("/add_campaign", methods=["GET", "POST"])
def add_campaign():
    return render_template("campaign_creation.html")


@campaign_bp.route("/campaign_name_list", methods=["GET"])
def campaign_name_list():
    return render_template("campaign_name_list.html", campaigns=campaign_list())


@campaign_bp.route("/get_default_values/<string:campaign_name>", methods=["GET"])
def get_default_values(campaign_name: str):
    if not campaign_name:
        return jsonify({"status": "failure", "message": "Campaign name is required"}), 400

    default_values = get_default_for_campaign(campaign_name)

    if not default_values:
        return jsonify({"status": "failure", "message": "Campaign not found"}), 404

    return jsonify(default_values)


@campaign_bp.route("/edit_campaign_row/<int:campaign_id>", methods=["POST"])
def edit_campaign_controller(campaign_id: int):
    data = request.json
    if data is None:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    success, message = edit_campaign_row(campaign_id, data)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"status": "error", "message": message}), 404
