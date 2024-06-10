from collections import defaultdict
from datetime import timedelta, date
from io import BytesIO
from typing import Any, Dict, List

import xlsxwriter
from sqlalchemy import Column, Date

from src.database.db import get_session
from src.repositories.campaign_repository import get_campaign_by_id, get_campaign_list
from src.repositories.statistics_repository import get_click_count, get_ga_data, get_ga_data_other, get_graph_data
from src.repositories.utm_link_repository import get_filtered_links, get_links_by_campaign


def campaign_list(list_type: bool = None) -> list[dict[str, Any]]:
    campaigns_data = []
    with get_session() as session:
        campaigns = get_campaign_list(session, list_type)
        for campaign in campaigns:
            campaign_data = {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_start_date": campaign.start_date,
                "campaign_url_by_default": campaign.url_by_default,
                "campaign_domain_by_default": campaign.domain_by_default,
                "campaign_hide": campaign.hide,
            }
            campaigns_data.append(campaign_data)
    return campaigns_data


def campaign_info(campaign_id: int) -> List[Dict[str, Any]] | None:
    links_data = []
    with get_session() as session:
        campaign = get_campaign_by_id(session, campaign_id)
        if not campaign:
            return None
        links = get_links_by_campaign(session, campaign.name)
        if not links:
            return None

        date_start_date: date = campaign.start_date
        date_delta_7: date = campaign.start_date + timedelta(days=7)
        date_delta_14: date = campaign.start_date + timedelta(days=14)
        date_delta_21: date = campaign.start_date + timedelta(days=21)

        for link in links:
            link_info = {
                "id": link.id,
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks_total": get_click_count(session, link.id),
                "clicks_1d": (
                    get_click_count(session, link.id, date_start_date, date_start_date) if campaign.start_date else 0
                ),
                "clicks_7d": (
                    get_click_count(session, link.id, date_start_date, date_delta_7) if campaign.start_date else 0
                ),
                "clicks_14d": (
                    get_click_count(
                        session,
                        link.id,
                        date_delta_7,
                        date_delta_14,
                    )
                    if campaign.start_date
                    else 0
                ),
                "clicks_21d": (
                    get_click_count(
                        session,
                        link.id,
                        date_delta_14,
                        date_delta_21,
                    )
                    if campaign.start_date
                    else 0
                ),
            }
            link_info.update(
                ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content)
            )
            links_data.append(link_info)

        campaign_contents = [link["campaign_content"] for link in links_data]
        campaign_sources_medium = [f'{link["campaign_source"]} / {link["campaign_medium"]}' for link in links_data]

        ga_other = get_ga_data_other_list(campaign.url_by_default, campaign_sources_medium, campaign_contents)

    return links_data + ga_other


def ga_data_format(
        url: str,
        campaign_source: str,
        campaign_medium: str,
        campaign_content: str | None,
) -> dict[str, object]:
    ga_info = {
        "ga_active_users": 0,
        "ga_sessions": 0,
        "ga_average_session_duration": 0,
        "bounce_rate": "0%",
    }

    with get_session() as session:
        ga_result = get_ga_data(session, url, f"{campaign_source} / {campaign_medium}", campaign_content)
        if ga_result:
            session_duration = (
                f"{round(ga_result.average_session_duration)}s"
                if ga_result.average_session_duration < 60
                else f"{round(ga_result.average_session_duration) // 60}m {round(ga_result.average_session_duration) % 60}s"
            )
            ga_info["ga_active_users"] = ga_result.active_users or 0
            ga_info["ga_sessions"] = ga_result.sessions or 0
            ga_info["ga_average_session_duration"] = session_duration or 0
            ga_info["bounce_rate"] = f"{round(ga_result.bounce_rate * 100, 2)}%" if ga_result.bounce_rate else "0%"
    return ga_info


def get_ga_data_other_list(url: Column[str] | str, source_medium: list, campaign_content: list) -> List[Dict[str, Any]]:
    with get_session() as session:
        ga_result = get_ga_data_other(session, url, source_medium, campaign_content)

        ga_info_list = []
        for row in ga_result:
            campaign_source, campaign_medium = (
                (row[1].split("/", 1) if "/" in row[1] else (row[1], "Unknown"))
                if row[1] != "(not set)"
                else ("Unknown", "Unknown")
            )
            session_duration = f"{round(row[4])}s" if row[4] < 60 else f"{round(row[4]) // 60}m {round(row[4]) % 60}s"
            ga_info = {
                "url": url,
                "campaign_content": row[0],
                "campaign_source": campaign_source,
                "campaign_medium": campaign_medium,
                "ga_active_users": row[2],
                "ga_sessions": row[3],
                "ga_average_session_duration": session_duration,
                "bounce_rate": f"{round(row[5] * 100, 2)}%" if row[5] else "0%",
            }
            ga_info_list.append(ga_info)

    return ga_info_list


def campaign_graph(campaign_id: int) -> dict:
    with get_session() as session:
        campaign = get_campaign_by_id(session, campaign_id)
        if campaign is not None:
            data = get_graph_data(session, campaign.name)
        graph_data: dict = defaultdict(lambda: defaultdict(dict))
        for record in data:
            source_medium, date_str = record[0], record[1].isoformat()
            graph_data[source_medium][date_str]["clicks"] = record[2] if record[2] is not None else 0
            graph_data[source_medium][date_str]["sessions"] = record[3] if record[3] is not None else 0

    return graph_data


def generate_campaign_excel(output: BytesIO, campaign_id: int) -> str | None:
    campaign_data: List[Dict[str, Any]] | None = campaign_info(campaign_id)
    if not campaign_data:
        return "Campaign is empty"

    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Campaign Info")

    headers = [
        "URL",
        "Campaign Content",
        "Campaign Source",
        "Campaign Medium",
        "Short ID",
        "Short Secure URL",
        "Clicks Total",
        "Clicks 1d",
        "Clicks 7d",
        "Clicks 14d",
        "Clicks 21d",
        "GA Active Users",
        "GA Sessions",
        "GA Average Session Duration",
        "Bounce Rate",
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    for row_num, data in enumerate(campaign_data, start=1):
        row = [
            data.get("url", ""),
            data.get("campaign_content", ""),
            data.get("campaign_source", ""),
            data.get("campaign_medium", ""),
            data.get("short_id", ""),
            data.get("short_secure_url", ""),
            data.get("clicks_total", ""),
            data.get("clicks_1d", ""),
            data.get("clicks_7d", ""),
            data.get("clicks_14d", ""),
            data.get("clicks_21d", ""),
            data.get("ga_active_users", ""),
            data.get("ga_sessions", ""),
            data.get("ga_average_session_duration", ""),
            data.get("bounce_rate", ""),
        ]
        for col, value in enumerate(row):
            worksheet.write(row_num, col, value)

    workbook.close()
    return None


def filtered_statistic(form_data: dict) -> list:
    with get_session() as session:
        links = get_filtered_links(session, form_data)

        links_data = []
        for link in links:
            link_info = {
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks": get_click_count(session, link.id, form_data["date_from"], form_data["date_to"]),
            }
            if None not in (link.url, link.campaign_source, link.campaign_medium, link.campaign_content):
                link_info.update(
                    ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content)
                )
            links_data.append(link_info)
    return links_data