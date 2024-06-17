from flask import Blueprint, render_template, request

from services import get_options_context, process_option_form

options = Blueprint(
    "options",
    __name__,
)


@options.route("/exclude-options", methods=["GET", "POST"])
def exclude_options():
    if request.method == "POST":
        process_option_form(request.form, "add")
    return render_template("manage_exclusions.html", **get_options_context("unique"))


@options.route("/manage-exclusions", methods=["GET", "POST"])
def manage_exclusions():
    if request.method == "POST":
        process_option_form(request.form, "delete")
    return render_template("manage_exclusions.html", **get_options_context("excluded"))
