from collections import defaultdict
from datetime import timedelta
from io import BytesIO
from typing import Any, List, Sequence

import xlsxwriter
from sqlalchemy import Column

from crud import (
    get_campaign_by_id,
    get_campaign_links,
    get_campaign_list,
    get_click_count,
    get_filtered_links,
    get_ga_data,
    get_ga_data_other,
    get_graph_data,
)
from database import get_db


def campaign_list(list_type: bool = None) -> list[dict[str, Any]]:
    campaigns_data = []
    with get_db() as db:
        campaigns = get_campaign_list(db, list_type)
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


def campaign_info(campaign_id: int) -> Sequence[Any]:
    links_data: List[dict] = []
    with get_db() as db:
        campaign = get_campaign_by_id(db, campaign_id)
        if not campaign:
            return links_data
        links = get_campaign_links(db, campaign.name)
        if not links:
            return links_data

        for link in links:
            link_info = {
                "id": link.id,
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks_total": get_click_count(db, link.id),
                "clicks_1d": (
                    get_click_count(db, link.id, campaign.start_date, campaign.start_date) if campaign.start_date else 0
                ),
                "clicks_7d": (
                    get_click_count(db, link.id, campaign.start_date, campaign.start_date + timedelta(days=7))
                    if campaign.start_date
                    else 0
                ),
                "clicks_14d": (
                    get_click_count(
                        db, link.id, campaign.start_date + timedelta(days=7), campaign.start_date + timedelta(days=14)
                    )
                    if campaign.start_date
                    else 0
                ),
                "clicks_21d": (
                    get_click_count(
                        db, link.id, campaign.start_date + timedelta(days=14), campaign.start_date + timedelta(days=21)
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
    url: Column[str] | str,
    campaign_source: Column[str] | str,
    campaign_medium: Column[str] | str,
    campaign_content: Column[str] | str,
) -> dict[str, object]:
    ga_info = {
        "ga_active_users": 0,
        "ga_sessions": 0,
        "ga_average_session_duration": 0,
        "bounce_rate": "0%",
    }

    with get_db() as db:
        ga_result = get_ga_data(db, url, f"{campaign_source} / {campaign_medium}", campaign_content)

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


def get_ga_data_other_list(url: Column[str] | str, source_medium: list, campaign_content: list) -> List[Any]:
    with get_db() as db:
        ga_result = get_ga_data_other(db, url, source_medium, campaign_content)

    ga_info_list = []
    for row in ga_result:
        campaign_source, campaign_medium = (
            (row[1].split("/", 1) if "/" in row[1] else (row[1], "Unknown"))
            if row[1] != "(not set)"
            else ("Unknown", "Unknown")
        )
        ga_info = {
            "url": url,
            "campaign_content": row[0],
            "campaign_source": campaign_source,
            "campaign_medium": campaign_medium,
            "ga_active_users": row[2],
            "ga_sessions": row[3],
            "ga_average_session_duration": row[4],
            "bounce_rate": f"{round(row[5] * 100, 2)}%" if row[5] else "0%",
        }
        ga_info_list.append(ga_info)

    return ga_info_list


def campaign_graph(campaign_id: int) -> dict:
    with get_db() as db:
        campaign = get_campaign_by_id(db, campaign_id)
        if campaign is not None:
            data = get_graph_data(db, campaign.name)
    graph_data: dict = defaultdict(lambda: defaultdict(dict))
    for record in data:
        source_medium, date_str = record[0], record[1].isoformat()
        graph_data[source_medium][date_str]["clicks"] = record[2] if record[2] is not None else 0
        graph_data[source_medium][date_str]["sessions"] = record[3] if record[3] is not None else 0

    return graph_data


def generate_campaign_excel(output: BytesIO, campaign_id: int):
    campaign_data = campaign_info(campaign_id)
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
            data["url"],
            data["campaign_content"],
            data["campaign_source"],
            data["campaign_medium"],
            data["short_id"],
            data["short_secure_url"],
            data["clicks_total"],
            data["clicks_1d"],
            data["clicks_7d"],
            data["clicks_14d"],
            data["clicks_21d"],
            data["ga_active_users"],
            data["ga_sessions"],
            data["ga_average_session_duration"],
            data["bounce_rate"],
        ]
        for col, value in enumerate(row):
            worksheet.write(row_num, col, value)

    workbook.close()


def filtered_statistic(form_data: dict) -> list:
    with get_db() as db:
        links = get_filtered_links(db, form_data)

        links_data = []
        for link in links:
            link_info = {
                "url": link.url,
                "campaign_content": link.campaign_content,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "short_id": link.short_id,
                "short_secure_url": link.short_secure_url,
                "clicks": get_click_count(db, link.id, form_data["date_from"], form_data["date_to"]),
            }
            if None not in (link.url, link.campaign_source, link.campaign_medium, link.campaign_content):
                link_info.update(
                    ga_data_format(link.url, link.campaign_source, link.campaign_medium, link.campaign_content)
                )
            links_data.append(link_info)
    return links_data
