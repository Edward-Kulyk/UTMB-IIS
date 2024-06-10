from datetime import datetime
from typing import Any, Dict, List

from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportResponse
from google.auth import load_credentials_from_file


class GoogleAnalyticsService:
    def __init__(self, service_account_file: str):
        self.credentials = load_credentials_from_file(service_account_file)[0]
        self.client = BetaAnalyticsDataClient(credentials=self.credentials)

    def run_report(self, request):
        return self.client.run_report(request)

    def process_response_graph(self, response: RunReportResponse, url: str) -> List[Dict[str, Any]]:
        return [
            {
                "session_source_medium": row.dimension_values[1].value,
                "url": url,
                "active_users": int(row.metric_values[0].value),
                "date": datetime.strptime(row.dimension_values[0].value, "%Y%m%d"),
                "sessions": int(row.metric_values[1].value),
            }
            for row in response.rows
        ]

    def process_response_table(self, response: RunReportResponse, url: str) -> List[Dict[str, Any]]:
        return [
            {
                "session_source_medium": row.dimension_values[0].value,
                "url": url,
                "active_users": int(row.metric_values[0].value),
                "average_session_duration": float(row.metric_values[1].value),
                "bounce_rate": float(row.metric_values[2].value),
                "sessions": int(row.metric_values[3].value),
                "content": row.dimension_values[2].value,
            }
            for row in response.rows
        ]
