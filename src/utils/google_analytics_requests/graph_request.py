from datetime import date, datetime

from google.analytics.data_v1beta import DateRange, Dimension, Filter, FilterExpression, Metric, RunReportRequest
from sqlalchemy import ColumnElement


# noinspection PyTypeChecker
def build_analytics_request_graph(
    property_id: str | ColumnElement[str],
    url: str | ColumnElement[str],
    start_date: datetime | ColumnElement[date],
    end_date: datetime | ColumnElement[date],
) -> RunReportRequest:
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="Date"),
            Dimension(name="sessionSourceMedium"),
            Dimension(name="landingPage"),
        ],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="landingPage",
                string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.EXACT, value=url),
            )
        ),
        metric_aggregations=["TOTAL"],
        limit=1000,
    )
    return request
