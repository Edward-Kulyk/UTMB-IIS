import json
import time
from datetime import datetime, timedelta

import requests
from app import db
from config import Config
from models import Campaign, ClicksDate, UTMLink
from sqlalchemy import not_


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
    print(long_url)
    return response.json()


def update_clicks_count():
    # Получаем ссылки и связанные кампании
    utm_links = UTMLink.query.join(Campaign, UTMLink.campaign_name == Campaign.name).filter(not_(Campaign.hide)).all()

    current_date = datetime.utcnow().date() + timedelta(days=1)

    for utm_link in utm_links:
        # Рассчитываем разницу между текущей датой и датой начала кампании
        date_diff = current_date - utm_link.campaign.start_date

        # Пропускаем итерацию цикла, если разница больше 28 дней
        if date_diff > timedelta(weeks=4):
            print(f"Пропускаем {utm_link.campaign_name}, так как разница между датами больше 4 недель.")
            continue

        print(utm_link.campaign_name)
        response_data = get_clicks_filter(utm_link.short_id, utm_link.campaign.start_date, current_date)
        process_clicks_data(utm_link.id, response_data)


def process_clicks_data(utm_link_id, click_data):
    if "clickStatistics" in click_data:
        datasets = click_data["clickStatistics"].get("datasets", [])
        for dataset in datasets:
            data = dataset.get("data", [])
            for click in data:
                click_date = datetime.strptime(click["x"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
                new_clicks_count = int(click["y"])

                # Проверяем, существует ли запись для данной даты и ссылки
                link_click_date = ClicksDate.query.filter_by(link_id=utm_link_id, date=click_date).first()

                if link_click_date:
                    # Если запись существует и новое количество кликов больше или равно старому, обновляем количество кликов
                    if new_clicks_count >= link_click_date.clicks_count:
                        link_click_date.clicks_count = new_clicks_count
                        print(f"Обновлено: {utm_link_id}, Дата: {click_date}, Клики: {new_clicks_count}")
                    else:
                        print(
                            f"Пропущено (новое значение меньше старого): {utm_link_id}, Дата: {click_date}, Старое значение: {link_click_date.clicks_count}, Новое значение: {new_clicks_count}"
                        )
                else:
                    # Если записи нет, создаем новую запись
                    link_click_date = ClicksDate(link_id=utm_link_id, date=click_date, clicks_count=new_clicks_count)
                    db.session.add(link_click_date)
                    print(f"Создано: {utm_link_id}, Дата: {click_date}, Клики: {new_clicks_count}")

        # Сохраняем изменения в базе данных
        db.session.commit()


def get_clicks_filter(short_id, startDate, endDate):
    url = f"https://api-v2.short.io/statistics/link/{short_id}"
    querystring = {"period": "custom", "tz": "UTC", "startDate": startDate, "endDate": endDate}

    headers = {"accept": "*/*", "authorization": Config.SHORT_IO_API_KEY}

    for attempt in range(8):  # Попытаемся до 5 раз при ошибке 429
        response = requests.get(url, headers=headers, params=querystring)
        print(response.json())
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


# def aggregate_clicks(short_ids, startDate, endDate):
#     clicks_aggregated = defaultdict(int)
#     clicks_by_short_id = {}
#     os_aggregated = defaultdict(int)
#     country_aggregated = defaultdict(int)  # New dictionary for country aggregation
#
#     for short_id in short_ids:
#         url = f"https://api-v2.short.io/statistics/link/{short_id}"
#         querystring = {"period": "custom", "tz": "UTC", 'startDate': startDate, "endDate": endDate}
#
#         headers = {
#             'accept': "*/*",
#             'authorization': Config.SHORT_IO_API_KEY
#         }
#
#         for attempt in range(6):  # Try up to 5 times on 429 error
#             response = requests.get(url, headers=headers, params=querystring)
#             print(response.json())
#             if response.status_code == 429:
#                 time.sleep(2 ** attempt)  # Exponential backoff
#             elif response.status_code == 200:
#                 data = response.json()
#                 clicks_by_short_id[short_id] = data.get("humanClicks", 0)
#                 for entry in data.get("clickStatistics", {}).get("datasets", [])[0].get("data", []):
#                     clicks_aggregated[entry["x"][:10]] += int(entry["y"])  # Aggregate clicks by dates
#                 for os_data in data.get('os', []):
#                     os_aggregated[os_data['os']] += os_data['score']
#                 for country_data in data.get('country', []):  # Correct key for country data
#                     country_aggregated[country_data['countryName']] += country_data['score']
#                 break  # Break the loop after a successful request
#             else:
#                 break  # Break the loop on other errors
#
#     # Convert data for chart usage
#     os_data_for_chart = [{'os': os, 'score': score} for os, score in os_aggregated.items()]
#     country_data_for_chart = [{'country': country, 'score': score} for country, score in country_aggregated.items()]
#     clicks_data = [{'x': date, 'y': clicks} for date, clicks in clicks_aggregated.items()]
#     return sorted(clicks_data, key=lambda x: x['x']), clicks_by_short_id, os_data_for_chart  # Sort data by date


def aggregate_clicks(short_ids, date_from, date_to):
    # Initialize dictionaries to store clicks data
    clicks_data = {}
    clicks_by_line = {}
    os_data_for_chart = {}

    # Query clicks data from the database
    clicks_query = (
        db.session.query(ClicksDate.link_id, ClicksDate.date, ClicksDate.clicks_count)
        .filter(ClicksDate.date.between(date_from, date_to))
        .filter(ClicksDate.link_id.in_(short_ids))
    )

    # Group clicks data by link_id and date
    clicks_results = clicks_query.all()

    for link_id, click_date, click_count in clicks_results:
        if link_id not in clicks_data:
            clicks_data[link_id] = {}
        clicks_data[link_id][click_date] = click_count

    # Aggregate clicks by line (link_id)
    for link_id, click_data in clicks_data.items():
        clicks_by_line[link_id] = sum(click_data.values())

    # # Get operating system data for each link from the database
    # os_query = db.session.query(ClicksDate.link_id, ClicksDate.date, ClicksDate.operating_system) \
    #     .filter(ClicksDate.date.between(date_from, date_to)) \
    #     .filter(ClicksDate.link_id.in_(short_ids))
    #
    # os_results = os_query.all()
    #
    # # Group OS data by link_id and date
    # for link_id, click_date, os in os_results:
    #     if link_id not in os_data_for_chart:
    #         os_data_for_chart[link_id] = {}
    #     if click_date not in os_data_for_chart[link_id]:
    #         os_data_for_chart[link_id][click_date] = {}
    #     os_data_for_chart[link_id][click_date][os] = os_data_for_chart[link_id][click_date].get(os, 0) + 1

    return clicks_data, clicks_by_line, os_data_for_chart


def edit_link(id):
    record = UTMLink.query.filter_by(id=id).first()
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


def delete_link(id):
    url = f"https://api.short.io/links/{id}"

    headers = {"authorization": Config.SHORT_IO_API_KEY}

    response = requests.request("DELETE", url, headers=headers)
    return response
