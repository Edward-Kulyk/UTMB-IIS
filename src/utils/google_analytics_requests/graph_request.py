from datetime import date, datetime

from google.analytics.data_v1beta import DateRange, Dimension, Filter, FilterExpression, Metric, RunReportRequest
from sqlalchemy import ColumnElement


# noinspection PyTypeChecker
def build_analytics_request(
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
            Dimension(name="sessionManualAdContent"),
        ],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ],
        date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="landingPage",
                string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.EXACT, value=url),
            )
        ),
        metric_aggregations=["TOTAL"],
    )
    return request
