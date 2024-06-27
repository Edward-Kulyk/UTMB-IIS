from io import BytesIO

from flask import Blueprint, render_template, request, send_file

from src.services.campaign_service import campaign_list
from src.services.option_service import get_options_context
from src.services.statistic_service import campaign_graph, campaign_info, filtered_statistic, generate_campaign_excel

statistics_bp = Blueprint(
    "statistics",
    __name__,
)


@statistics_bp.route("/campaigns", methods=["GET"])
def campaigns_statistics():
    return render_template("campaigns.html", campaign_list=campaign_list(False))


@statistics_bp.route("/campaigns/api/table/<int:campaign_id>", methods=["GET"])
def campaigns_data(campaign_id: int):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    print(f"Received start date: {start_date} and end date: {end_date, campaign_id}")
    return campaign_info(campaign_id, start_date, end_date)


@statistics_bp.route("/campaigns/api/graph/<int:campaign_id>", methods=["GET"])
def campaigns_graph_info(campaign_id: int):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    print(f"Received start date: {start_date} and end date: {end_date, campaign_id}")
    return campaign_graph(campaign_id, start_date, end_date)


@statistics_bp.route("/campaigns/api/quarter_table/<int:quarter><int:year>", methods=["GET"])
def quarter_overview_table(quarter: int, year: int):
    return quarter_info(quarter, year)


@statistics_bp.route("/campaigns/api/quarter_graph/<int:quarter><int:year>", methods=["GET"])
def quarter_overview_graph(campaign_id: int):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    print(f"Received start date: {start_date} and end date: {end_date, campaign_id}")
    return quarter_graph(campaign_id, start_date, end_date)


@statistics_bp.route("/campaigns/api/query/<int:campaign_id>", methods=["GET"])
def query(campaign_id: int):
    output = BytesIO()
    generate_campaign_excel(output, campaign_id)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="query_result.xlsx")


@statistics_bp.route("/filter_setting", methods=["GET", "POST"])
def filter_setting():
    if request.method == "POST":
        links_data = filtered_statistic(request.form)
        return render_template("filtered_utm.html", link_info=links_data)
    return render_template("filter_setting.html", **get_options_context("unique"))
