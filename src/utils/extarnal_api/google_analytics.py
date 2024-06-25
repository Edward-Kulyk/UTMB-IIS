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

    @staticmethod
    def process_response(response: RunReportResponse, url: str) -> List[Dict[str, Any]]:
        return [
            {
                "date": datetime.strptime(row.dimension_values[0].value, "%Y%m%d"),
                "session_source_medium": row.dimension_values[1].value,
                "url": url,
                "content": row.dimension_values[3].value,

                "active_users": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "bounce_rate": int(round(float(row.metric_values[2].value), 2) * 100),
                "average_session_duration": int(round(float(row.metric_values[3].value), 2) * 100),
            }
            for row in response.rows
        ]
