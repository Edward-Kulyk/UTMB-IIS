from typing import Dict

from config import Config
from flask import Blueprint, jsonify, render_template, request
from pydantic_core import ValidationError

from src.factories.utm_link_factory import UTMLinkFactory
from src.forms.link_creation_form import LinkCreationForm
from src.repositories.utm_link_repository import delete_link
from src.services.campaign_service import edit_campaign_row
from src.services.option_service import get_options_context
from src.services.utm_link_service import create_link
from src.utils.extarnal_api.short_io import ShortLinkManager

link = Blueprint(
    "link",
    __name__,
)

short_link_service = ShortLinkManager(api_key=Config.SHORT_IO_API_KEY)
utm_link_factory = UTMLinkFactory(short_link_service)


@link.route("/", methods=["GET", "POST"])
def link_creation():
    context = get_options_context("unique")
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            form = LinkCreationForm(**form_data)
        except ValidationError as e:
            context.update({"error_message": e.errors()})
            return render_template("index.html", **context)

        response: Dict[str] = create_link(
            form.url,
            form.campaign_source,
            form.campaign_content,
            form.domain,
            form.campaign_medium,
            form.campaign_name,
            form.slug,
        )
        context.update(response)

    return render_template("index.html", **context)


@link.route("/edit-campaign-row/<int:campaign_id>", methods=["UPDATE"])
def edit_row(campaign_id: int):
    data = request.json
    if data is None:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    success, message = edit_campaign_row(campaign_id, data)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"status": "error", "message": message}), 404


@link.route("/link/api/<string:short_link_id>", methods=["DELETE"])
def delete_link_api(short_link_id: str):
    return delete_link(short_link_id)
