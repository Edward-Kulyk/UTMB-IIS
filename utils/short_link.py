import json
import time
from datetime import datetime, timedelta

import requests

from config import Config
from crud import get_clicks_date, get_link, get_utm_links
from crud.link_crud import add_clicks_date, update_clicks_date
from database import get_db


def create_short_link(domain, slug, long_url):
    api_url = "https://api.short.io/links"
    headers = {
        "Content-Type": "application/json",
        "authorization": Config.SHORT_IO_API_KEY,
    }
    if slug == "":
        data = {"originalURL": long_url, "domain": domain, "title": "ACCZ | API Created"}
    else:
        data = {"originalURL": long_url, "domain": domain, "path": slug, "title": "ACCZ | API Created"}

    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    return response.json()


def update_clicks_count():
    with get_db() as db:
        utm_links = get_utm_links(db)
        current_date = datetime.now().date() + timedelta(days=1)

        for utm_link in utm_links:
            date_diff = current_date - utm_link.campaign.start_date

            if date_diff > timedelta(weeks=4):
                continue

            response_data = get_clicks_filter(utm_link.short_id, utm_link.campaign.start_date, current_date)
            process_clicks_data(utm_link.id, response_data)


def process_clicks_data(utm_link_id, click_data):
    with get_db() as db:
        if "clickStatistics" in click_data:
            datasets = click_data["clickStatistics"].get("datasets", [])
            for dataset in datasets:
                data = dataset.get("data", [])
                for click in data:
                    click_date = datetime.strptime(click["x"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
                    new_clicks_count = int(click["y"])

                    link_click_date = get_clicks_date(db, utm_link_id, click_date)

                    if link_click_date:
                        if new_clicks_count > link_click_date.clicks_count:
                            update_clicks_date(db, link_click_date, new_clicks_count)
                            print("Обновились")
                    else:
                        add_clicks_date(db, utm_link_id, click_date, new_clicks_count)
                        print("добавились")


def get_clicks_filter(short_id, startDate, endDate):
    url = f"https://api-v2.short.io/statistics/link/{short_id}"
    querystring = {"period": "custom", "tz": "UTC", "startDate": startDate, "endDate": endDate}

    headers = {"accept": "*/*", "authorization": Config.SHORT_IO_API_KEY}

    for attempt in range(8):  # Попытаемся до 5 раз при ошибке 429
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 429:
            time.sleep(2**attempt)  # Экспоненциальная задержка
        elif response.status_code == 200:
            return response.json()
        else:
            return 0  # Возвращаем 0 при других ошибках


def get_clicks_total(short_id):
    url = f"https://api-v2.short.io/statistics/link/{short_id}"
    querystring = {"period": "total", "tz": "UTC+2"}

    headers = {"accept": "*/*", "authorization": Config.SHORT_IO_API_KEY}

    for attempt in range(6):  # Попытаемся до 5 раз при ошибке 429
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 429:
            time.sleep(2**attempt)  # Экспоненциальная задержка
        elif response.status_code == 200:
            clicks = response.json().get("humanClicks", 0)
            return clicks
        else:
            return 0  # Возвращаем 0 при других ошибках


def edit_link(link_id: int):
    with get_db() as db:
        record = get_link(db, link_id)
    if record is None:
        return
    url = f"https://api.short.io/links/{record.short_id}"
    payload = json.dumps(
        {
            "allowDuplicates": False,
            "domain": record.domain,
            "path": record.slug,
            "originalURL": f"{record.url}?utm_campaign={record.campaign_name.replace(' ', '+')}&utm_medium={record.campaign_medium.replace(' ', '+')}&utm_source={record.campaign_source.replace(' ', '+')}&utm_content={record.campaign_content.replace(' ', '+')}",
        }
    )
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": Config.SHORT_IO_API_KEY,
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    return response


def delete_link_shot_io(link_id: str):
    url = f"https://api.short.io/links/{link_id}"

    headers = {"authorization": Config.SHORT_IO_API_KEY}

    response = requests.request("DELETE", url, headers=headers)
    return response
