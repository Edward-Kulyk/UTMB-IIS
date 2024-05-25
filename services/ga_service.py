from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse

from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportResponse
from google.auth import credentials, load_credentials_from_file

from config import Config
from crud import get_campaign_list, insert_or_update_data
from database import get_session
from models import Campaign, GoogleAnalyticsDataGraph, GoogleAnalyticsDataTable
from utils.ga4_requests import build_analytics_request_graph, build_analytics_request_table


def get_service_account_credentials() -> credentials.Credentials:
    ga_credentials, _ = load_credentials_from_file(Config.SERVICE_ACCOUNT_FILE)
    return ga_credentials


def get_analytics_client(ga_credentials) -> BetaAnalyticsDataClient:
    return BetaAnalyticsDataClient(credentials=ga_credentials)


def analytics_data() -> None:
    ga_credentials = get_service_account_credentials()
    client = get_analytics_client(ga_credentials)

    with get_session() as session:
        campaigns = get_campaign_list(session, False)

        for campaign in campaigns:
            for property_id in Config.PROPERTY_IDS:
                start_date = campaign.start_date - timedelta(weeks=2)
                end_date = campaign.start_date + timedelta(weeks=3)

                parsed_url = urlparse(str(campaign.url_by_default))
                path = parsed_url.path.rstrip("/")

                request_graph = build_analytics_request_graph(property_id, path, start_date, end_date)
                response_graph = client.run_report(request_graph)
                graph_data = process_response_graph(response_graph, campaign)

                for data in graph_data:
                    filters = {
                        "session_source_medium": data["session_source_medium"],
                        "url": data["url"],
                        "date": data["date"].date(),
                    }
                    insert_or_update_data(session, GoogleAnalyticsDataGraph, filters, data)
                session.commit()

                request_table = build_analytics_request_table(property_id, path, start_date, end_date)
                response_table = client.run_report(request_table)
                table_data = process_response_table(response_table, campaign)

                for data in table_data:
                    filters = {
                        "session_source_medium": data["session_source_medium"],
                        "url": data["url"],
                        "content": data["content"],
                    }
                    insert_or_update_data(session, GoogleAnalyticsDataTable, filters, data)
                session.commit()


def process_response_graph(response: RunReportResponse, campaign: Campaign) -> List[Dict[str, Any]]:
    url = campaign.url_by_default
    data_to_insert = [
        {
            "session_source_medium": row.dimension_values[1].value,
            "url": url,
            "active_users": int(row.metric_values[0].value),
            "date": datetime.strptime(row.dimension_values[0].value, "%Y%m%d"),
            "sessions": int(row.metric_values[1].value),
        }
        for row in response.rows
    ]
    return data_to_insert


def process_response_table(response: RunReportResponse, campaign: Campaign) -> List[Dict[str, Any]]:
    url = campaign.url_by_default
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
