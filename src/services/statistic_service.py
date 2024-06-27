from collections import defaultdict
from datetime import timedelta, datetime
from io import BytesIO
from typing import Any, Dict, List, Sequence, Optional
from urllib.parse import urlparse

import xlsxwriter

from config import Config
from src.database.db import get_session
from src.database.models import GoogleAnalyticsData, ClicksDate, Campaign
from src.repositories import campaign_repository, statistics_repository, utm_link_repository
from src.utils.extarnal_api.google_analytics import GoogleAnalyticsService
from src.utils.extarnal_api.short_io import ShortLinkManager
from src.utils.google_analytics_requests.graph_request import build_analytics_request


def update_ga() -> None:
    with get_session() as session:
        campaigns = campaign_repository.get_campaign_list(session)
        service = GoogleAnalyticsService(Config.SERVICE_ACCOUNT_FILE)

        for property_id in Config.PROPERTY_IDS:
            process_property(service, property_id, campaigns, session)


def process_property(service: GoogleAnalyticsService, property_id: str, campaigns: Sequence[Campaign], session) -> None:
    for campaign in campaigns:
        process_campaign(service, property_id, campaign, session)


def process_campaign(service: GoogleAnalyticsService, property_id: str, campaign: Campaign, session) -> None:
    start_date = campaign.start_date - timedelta(weeks=10)
    end_date = campaign.start_date + timedelta(weeks=13)
    parsed_url = urlparse(campaign.url_by_default).path[:-1]

    analytics_request = build_analytics_request(property_id, parsed_url, start_date, end_date)
    info = service.run_report(analytics_request)
    ga_data = service.process_response(info, campaign.url_by_default)

    for data in ga_data:
        update_ga_data(session, data)


def update_ga_data(session, data: Dict[str, Any]) -> None:
    filters = {
        "session_source_medium": data["session_source_medium"],
        "content": data["content"],
        "url": data["url"],
        "date": data["date"].date(),
    }
    statistics_repository.insert_or_update_data(session, GoogleAnalyticsData, filters, data)


def get_click_data() -> None:
    with get_session() as session:
        campaigns = campaign_repository.get_campaign_list(session)
        sm = ShortLinkManager(Config.SHORT_IO_API_KEY)

        for campaign in campaigns:
            for link in campaign.links:
                response = sm.get_clicks_filter(link.short_id, campaign.start_date - timedelta(weeks=4),
                                                campaign.start_date + timedelta(weeks=8))
                process_clicks_data(session, link.id, response)


def process_clicks_data(session, link_id: int, click_data: Dict[str, Any]) -> None:
    datasets = click_data.get('clickStatistics', {}).get('datasets', [])

    for dataset in datasets:
        for click in dataset.get('data', []):
            process_single_click(session, link_id, click)


def process_single_click(session, link_id: int, click: Dict[str, Any]) -> None:
    click_date = datetime.strptime(click['x'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
    new_clicks_count = int(click['y'])
    link_click_date = statistics_repository.get_clicks_data(session, link_id, click_date)

    if link_click_date:
        update_existing_click(link_id, click_date, new_clicks_count, link_click_date)
    else:
        create_new_click(session, link_id, click_date, new_clicks_count)


def update_existing_click(link_id: int, click_date: datetime.date, new_clicks_count: int, link_click_date) -> None:
    if new_clicks_count > link_click_date.clicks_count:
        link_click_date.clicks_count = new_clicks_count


def create_new_click(session, link_id: int, click_date: datetime.date, new_clicks_count: int) -> None:
    link_click_date = ClicksDate(link_id=link_id, date=click_date, clicks_count=new_clicks_count)
    statistics_repository.add_clicks_data(session, link_click_date)
    print(f"Created: {link_id}, Date: {click_date}, Clicks: {new_clicks_count}")


def campaign_list(list_type: Optional[bool] = None) -> List[Dict[str, Any]]:
    with get_session() as session:
        campaigns = campaign_repository.get_campaign_list(session, list_type)
        return [
            {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_start_date": campaign.start_date,
                "campaign_url_by_default": campaign.url_by_default,
                "campaign_domain_by_default": campaign.domain_by_default,
                "campaign_hide": campaign.hide,
            }
            for campaign in campaigns
        ]


def campaign_info(campaign_id: int, start_date: Optional[datetime.date] = None,
                  end_date: Optional[datetime.date] = None) -> Optional[List[Dict[str, Any]]]:
    with get_session() as session:
        campaign = campaign_repository.get_campaign_by_id(session, campaign_id)
        if not campaign:
            return None

        links = utm_link_repository.get_links_by_campaign(session, campaign.name)
        if not links:
            return None

        start_date = start_date or (campaign.start_date - timedelta(weeks=10))
        end_date = end_date or (campaign.start_date + timedelta(weeks=13))

        links_data = []
        for link in links:
            link_info = {
                "id": link.id,
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks_total": statistics_repository.get_click_count(session, link.id, start_date, end_date),
            }
            link_info.update(
                ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content, start_date,
                               end_date))
            links_data.append(link_info)

        campaign_contents = [link["campaign_content"] for link in links_data]
        campaign_sources_medium = [f'{link["campaign_source"]} / {link["campaign_medium"]}' for link in links_data]

        ga_other = get_ga_data_other_list(campaign.url_by_default, campaign_sources_medium, campaign_contents,
                                          start_date, end_date)

    return links_data + ga_other


def ga_data_format(
        url: str,
        campaign_source: str,
        campaign_medium: str,
        campaign_content: Optional[str],
        start_date: datetime.date,
        end_date: datetime.date
) -> Dict[str, Any]:
    ga_info = {
        "ga_active_users": 0,
        "ga_sessions": 0,
        "ga_average_session_duration": "0s",
        "bounce_rate": "0%",
    }

    with get_session() as session:
        result = statistics_repository.get_ga_data(session, url, f"{campaign_source} / {campaign_medium}",
                                                   campaign_content, start_date, end_date)
        if result:
            users, sessions, session_duration, bounce_rate = result[0]

            ga_info["ga_active_users"] = users or 0
            ga_info["ga_sessions"] = sessions or 0
            ga_info["ga_average_session_duration"] = format_duration(session_duration)
            ga_info["bounce_rate"] = f"{round(bounce_rate, 2)}%" if bounce_rate else "0%"

    return ga_info


def format_duration(duration: float) -> str:
    if duration < 60:
        return f"{round(duration)}s"
    return f"{round(duration) // 60}m {round(duration) % 60}s"


def get_ga_data_other_list(url: str, source_medium: List[str], campaign_content: List[str], start_date: datetime.date,
                           end_date: datetime.date) -> List[Dict[str, Any]]:
    with get_session() as session:
        ga_result = statistics_repository.get_ga_data_other(session, url, source_medium, campaign_content, start_date,
                                                            end_date)

        return [
            {
                "url": url,
                "campaign_content": row[2],
                "campaign_source": row[0].split("/", 1)[0] if row[0] != "(not set)" else "Unknown",
                "campaign_medium": row[0].split("/", 1)[1] if "/" in row[0] and row[0] != "(not set)" else "Unknown",
                "ga_active_users": row[3],
                "ga_sessions": row[4],
                "ga_average_session_duration": format_duration(row[5]),
                "bounce_rate": f"{round(row[6], 2)}%" if row[6] else "0%",
            }
            for row in ga_result
        ]


def campaign_graph(campaign_id: int, start_date: Optional[datetime.date] = None,
                   end_date: Optional[datetime.date] = None) -> Dict[str, Dict[str, Dict[str, int]]]:
    with get_session() as session:
        campaign = campaign_repository.get_campaign_by_id(session, campaign_id)
        if not campaign:
            return {}

        start_date = start_date or (campaign.start_date - timedelta(weeks=10))
        end_date = end_date or (campaign.start_date + timedelta(weeks=13))

        data = statistics_repository.get_graph_data(session, campaign.name, start_date, end_date)

        graph_data: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
        for source_medium, date, clicks, sessions in data:
            date_str = date.isoformat()
            graph_data[source_medium][date_str]["clicks"] = clicks or 0
            graph_data[source_medium][date_str]["sessions"] = sessions or 0

    return graph_data


def generate_campaign_excel(output: BytesIO, campaign_id: int) -> Optional[str]:
    campaign_data = campaign_info(campaign_id)
    if not campaign_data:
        return "Campaign is empty"

    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Campaign Info")

    headers = [
        "URL", "Campaign Content", "Campaign Source", "Campaign Medium",
        "Short ID", "Short Secure URL", "Clicks Total", "Clicks 1d",
        "Clicks 7d", "Clicks 14d", "Clicks 21d", "GA Active Users",
        "GA Sessions", "GA Average Session Duration", "Bounce Rate",
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    for row_num, data in enumerate(campaign_data, start=1):
        row = [
            data.get(key, "") for key in [
                "url", "campaign_content", "campaign_source", "campaign_medium",
                "short_id", "short_secure_url", "clicks_total", "clicks_1d",
                "clicks_7d", "clicks_14d", "clicks_21d", "ga_active_users",
                "ga_sessions", "ga_average_session_duration", "bounce_rate",
            ]
        ]
        for col, value in enumerate(row):
            worksheet.write(row_num, col, value)

    workbook.close()
    return None


def filtered_statistic(form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    with get_session() as session:
        links = utm_link_repository.get_filtered_links(session, form_data)

        return [
            {
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks": statistics_repository.get_click_count(session, link.id, form_data["date_from"],
                                                                form_data["date_to"]),
                **ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content,
                                 form_data["date_from"], form_data["date_to"])
            }
            for link in links
            if None not in (link.url, link.campaign_source, link.campaign_medium, link.campaign_content)
        ]


def quarter_info(year, quarter):
    with get_session() as session:
        start_date, end_date = get_quarter_dates(year, quarter)
        campaigns = campaign_repository.get_campaign_list_in_date_range(session, start_date, end_date)
        if not campaigns:
            return None
        campaigns_info = []
        for campaign in campaigns:
            link_info = {
                "id": campaign.id,
                "url": campaign.url_by_default,
                "campaign_link_count": len(campaign.links),

                "clicks_total": statistics_repository.get_click_count(session, link.id, start_date, end_date),
            }
            link_info.update(
                ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content,
                               start_date,
                               end_date))
            links_data.append(link_info)




def get_quarter_dates(year, quarter):
    if quarter == 1:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 3, 31)
    elif quarter == 2:
        start_date = datetime(year, 4, 1)
        end_date = datetime(year, 6, 30)
    elif quarter == 3:
        start_date = datetime(year, 7, 1)
        end_date = datetime(year, 9, 30)
    elif quarter == 4:
        start_date = datetime(year, 10, 1)
        end_date = datetime(year, 12, 31)
    else:
        raise ValueError("Quarter must be between 1 and 4")

    return start_date, end_date
