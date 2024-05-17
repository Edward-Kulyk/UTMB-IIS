from google.analytics.data_v1beta.types import DateRange, Dimension, Filter, FilterExpression, Metric, RunReportRequest


def build_analytics_request_graph(property_id, url, start_date, end_date):
    # Формируем базовый запрос к Google Analytics
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


def build_analytics_request_table(property_id, url, start_date, end_date):
    # Формируем базовый запрос к Google Analytics
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionSourceMedium"),
            Dimension(name="landingPage"),
            Dimension(name="sessionManualAdContent"),
        ],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
            Metric(name="sessions"),
        ],
        date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="landingPage",
                string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.EXACT, value=url),
            )
        ),
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        metric_aggregations=["TOTAL"],
        limit=30,
    )
    return request
