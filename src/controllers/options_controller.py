from flask import Blueprint, render_template, request
from pydantic_core import ValidationError

from src.forms.option_schemas import ManageExclusionsForm
from src.services.option_service import get_options_context, process_option_form

option_bp = Blueprint(
    "options",
    __name__,
)


@option_bp.route("/exclude-options", methods=["GET", "POST"])
def exclude_options():
    if request.method == "POST":
        form_data = request.form.to_dict(flat=False)
        try:
            validated_data = ManageExclusionsForm(**form_data)
            process_option_form(validated_data.dict(), "add")
        except ValidationError as e:
            return render_template("manage_exclusions.html", **get_options_context("unique"), errors=e.errors())
    return render_template("manage_exclusions.html", **get_options_context("unique"))


@option_bp.route("/manage-exclusions", methods=["GET", "POST"])
def manage_exclusions():
    if request.method == "POST":
        form_data = request.form.to_dict(flat=False)
        try:
            validated_data = ManageExclusionsForm(**form_data)
            process_option_form(validated_data.dict(), "delete")
        except ValidationError as e:
            return render_template("manage_exclusions.html", **get_options_context("excluded"), errors=e.errors())
    return render_template("manage_exclusions.html", **get_options_context("excluded"))
