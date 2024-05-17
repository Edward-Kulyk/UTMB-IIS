from datetime import timedelta

import xlsxwriter as xlsxwriter
from app import db
from models import ClicksDate, GoogleAnalyticsDataGraph, GoogleAnalyticsDataTable, UTMLink
from sqlalchemy import and_, func


def get_top_5_source_medium_for_campaign(campaign_url):
    # Выбираем все ссылки из UTMLink, где URL равен переданному значению
    links = UTMLink.query.filter_by(url=campaign_url).all()

    # Создаем словарь для суммирования кликов по source_medium
    clicks_data = {}

    # Считаем сумму кликов для каждого source_medium
    for link in links:
        for click in link.clicks:
            source_medium = f"{link.campaign_source} / {link.campaign_medium}"
            if source_medium not in clicks_data:
                clicks_data[source_medium] = 0
            clicks_data[source_medium] += click.clicks_count

    # Сортируем source_medium по убыванию количества кликов и берем только топ 5
    top_5_source_medium = sorted(clicks_data.items(), key=lambda x: x[1], reverse=True)[:5]

    # Возвращаем топ 5 source_medium и соответствующее количество кликов
    return top_5_source_medium


def get_top_5_source_medium_from_ga4(url):
    # Запросим топ 5 source_medium и их суммарное количество сессий из второй таблицы
    top_source_medium = (
        db.session.query(
            GoogleAnalyticsDataGraph.session_source_medium,
            func.sum(GoogleAnalyticsDataGraph.sessions).label("total_sessions"),
        )
        .filter_by(url=url)
        .group_by(GoogleAnalyticsDataGraph.session_source_medium)
        .order_by(func.sum(GoogleAnalyticsDataGraph.sessions).desc())
        .limit(5)
        .all()
    )
    return top_source_medium


def get_sessions_and_dates_for_campaign(url, source_mediums):
    # Получаем ссылки, у которых URL совпадает с переданным значением
    links = UTMLink.query.filter_by(url=url).all()

    # Создаем список для хранения кликов и даты
    clicks_and_dates = []

    # Проходим по каждой ссылке
    for link in links:
        # Проверяем, есть ли source_medium текущей ссылки в списке top_5_source_medium_combined
        source_medium = f"{link.campaign_source} / {link.campaign_medium}"
        if source_medium in source_mediums:
            # Получаем клики и дату для этой ссылки
            for click in link.clicks:
                clicks_and_dates.append(
                    {
                        "session_source_medium": source_medium,
                        "clicks": click.clicks_count,
                        "date": click.date.strftime("%Y-%m-%d"),  # Преобразуем дату в строку
                    }
                )

    return clicks_and_dates


def get_sessions_and_dates_from_ga_graph(url, source_mediums):
    # Выполняем запрос к таблице Google Analytics Data Graph для указанного URL и source_mediums
    query_results = (
        GoogleAnalyticsDataGraph.query.filter_by(url=url)
        .filter(GoogleAnalyticsDataGraph.session_source_medium.in_(source_mediums))
        .all()
    )

    # Создаем список для хранения сессий и даты
    sessions_and_dates = []

    # Проходим по каждому результату запроса
    for result in query_results:
        # Добавляем сессии и дату в список
        sessions_and_dates.append(
            {
                "source_medium": result.session_source_medium,
                "sessions": result.sessions,
                "date": result.date.strftime("%Y-%m-%d"),  # Преобразуем дату в строку
            }
        )

    return sessions_and_dates


def get_campaign_info(campaign):
    # Агрегация данных по кампании
    campaign_clicks_total = (
        ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
        .filter(ClicksDate.link.has(UTMLink.campaign == campaign))
        .scalar()
        or 0
    )

    campaign_clicks_1d = (
        ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
        .filter(ClicksDate.link.has(UTMLink.campaign == campaign), ClicksDate.date == campaign.start_date)
        .scalar()
        or 0
    )

    campaign_clicks_7d = (
        ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
        .filter(
            ClicksDate.link.has(UTMLink.campaign == campaign),
            and_(ClicksDate.date > campaign.start_date, ClicksDate.date <= campaign.start_date + timedelta(days=7)),
        )
        .scalar()
        or 0
    )

    campaign_clicks_14d = (
        ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
        .filter(
            ClicksDate.link.has(UTMLink.campaign == campaign),
            and_(
                ClicksDate.date > campaign.start_date + timedelta(days=7),  # Следующий день после 7-го
                ClicksDate.date <= campaign.start_date + timedelta(days=14),  # До конца 14-го дня
            ),
        )
        .scalar()
        or 0
    )

    campaign_clicks_21d = (
        ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
        .filter(
            ClicksDate.link.has(UTMLink.campaign == campaign),
            and_(
                ClicksDate.date > campaign.start_date + timedelta(days=14),  # Следующий день после 14-го
                ClicksDate.date <= campaign.start_date + timedelta(days=21),  # До конца 21-го дня
            ),
        )
        .scalar()
        or 0
    )

    campaign_info = {
        "campaign_name": campaign.name,
        "start_date": campaign.start_date,
        "clicks_total": campaign_clicks_total,
        "clicks_1d": campaign_clicks_1d,
        "clicks_7d": campaign_clicks_7d,
        "clicks_14d": campaign_clicks_14d,
        "clicks_21d": campaign_clicks_21d,
        "ga_active_users": 0,
        "ga_sessions": 0,
        "links": [],
    }
    links = UTMLink.query.filter_by(campaign_name=campaign.name).all()
    ga_active_users = 0
    ga_sessions = 0
    for link in links:
        link_info = {
            "url": link.url,
            "campaign_content": link.campaign_content,
            "campaign_source": link.campaign_source,
            "campaign_medium": link.campaign_medium,
            "short_id": link.short_id,
            "short_secure_url": link.short_secure_url,
            "clicks_total": 0,
            "clicks_1d": 0,
            "clicks_7d": 0,
            "clicks_14d": 0,
            "clicks_21d": 0,
            "ga_active_users": 0,
            "ga_sessions": 0,
        }
        source_medium = f"{link.campaign_source} / {link.campaign_medium}"
        ga_info = GoogleAnalyticsDataTable.query.filter_by(
            url=campaign.url_by_default, session_source_medium=source_medium, content=link.campaign_content
        ).first()
        if ga_info:
            link_info["ga_active_users"] = ga_info.active_users
            link_info["ga_sessions"] = ga_info.sessions

            if ga_info.average_session_duration < 60:
                session_duration = f"{round(ga_info.average_session_duration)}s"
            else:
                session_duration = (
                    f"{round(ga_info.average_session_duration) // 60}m {round(ga_info.average_session_duration) % 60}s"
                )
            link_info["ga_average_session_duration"] = session_duration
            link_info["bounce_rate"] = str(round(ga_info.bounce_rate * 100, 2)) + "%"
            ga_active_users += ga_info.active_users
            ga_sessions += ga_info.sessions

        clicks = ClicksDate.query.filter_by(link_id=link.id).all()
        for click in clicks:
            if click.link.campaign.start_date == click.date:
                link_info["clicks_1d"] += click.clicks_count
            if (
                click.link.campaign.start_date + timedelta(days=1)
                <= click.date
                <= click.link.campaign.start_date + timedelta(days=7)
            ):
                link_info["clicks_7d"] += click.clicks_count
            if (
                click.link.campaign.start_date + timedelta(days=7)
                < click.date
                <= click.link.campaign.start_date + timedelta(days=14)
            ):
                link_info["clicks_14d"] += click.clicks_count
            if (
                click.link.campaign.start_date + timedelta(days=14)
                < click.date
                <= click.link.campaign.start_date + timedelta(days=21)
            ):
                link_info["clicks_21d"] += click.clicks_count
            if click.link.campaign.start_date <= click.date:
                link_info["clicks_total"] += click.clicks_count

        campaign_info["links"].append(link_info)
        campaign_info["ga_active_users"] = ga_active_users
        campaign_info["ga_sessions"] = ga_sessions
    return campaign_info


def get_graph_info(campaign):
    # Создадим структуру данных для хранения информации о кампании, кликах, сессиях и датах
    campaign_data = {"campaign_name": campaign.name, "start_date": campaign.start_date, "data": []}

    # Получим топ 5 source_medium для данной кампании из Google Analytics 4 и UTMLinks
    # ga4 = get_top_5_source_medium_from_ga4(campaign.url_by_default)
    ga4 = []
    clicks = get_top_5_source_medium_for_campaign(campaign.url_by_default)

    all_source_medium = set(
        [source_medium[0] for source_medium in ga4] + [source_medium[0] for source_medium in clicks]
    )

    # Преобразуем в список и сохраняем в переменную top_5_source_medium_combined
    top_5_source_medium_combined = list(all_source_medium)

    # Получим сессии и даты из Google Analytics Data Graph для текущей кампании
    sessions_and_dates_ga_graph = get_sessions_and_dates_from_ga_graph(
        campaign.url_by_default, top_5_source_medium_combined
    )
    # Получим сессии и даты из таблицы ClicksDate для текущей кампании
    sessions_and_dates_clicks = get_sessions_and_dates_for_campaign(
        campaign.url_by_default, top_5_source_medium_combined
    )

    start_date = campaign.start_date - timedelta(weeks=2)
    end_date = campaign.start_date + timedelta(weeks=3)

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    date_range = [date.strftime("%Y-%m-%d") for date in date_range]
    # Перебор каждой комбинации источника/среды
    for source_medium in top_5_source_medium_combined:
        # Перебор каждой даты в интервале
        for date in date_range:
            # Инициализация данных для текущей комбинации и даты
            date_data = {"date": date, "session_source_medium": source_medium, "sessions": 0, "clicks": 0}

            # Поиск данных о сессиях из Google Analytics Data Graph
            for session_data in sessions_and_dates_ga_graph:
                if session_data["date"] == date and session_data["source_medium"] == source_medium:
                    date_data["sessions"] += session_data["sessions"]

            # Поиск данных о кликах из таблицы ClicksDate
            for click_data in sessions_and_dates_clicks:
                if click_data["date"] == date and click_data["session_source_medium"] == source_medium:
                    date_data["clicks"] += click_data["clicks"]

            # Добавление данных в структуру кампании
            campaign_data["data"].append(date_data)

    return campaign_data


def generate_campaign_excel(campaign_info, graph_info, output):
    # Создаем объект xlsxwriter для записи в буфер
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # Добавляем лист для данных о кампании
    worksheet = workbook.add_worksheet("Campaign Data")

    # Записываем заголовки для таблицы
    headers = [
        "URL",
        "Campaign Content",
        "Campaign Source",
        "Campaign Medium",
        "Short ID",
        "Short Secure URL",
        "Clicks 24h",
        "Clicks W1",
        "Clicks W2",
        "Clicks W3",
        "Total Clicks",
        "GA Active Users",
        "GA Sessions",
        "Avg Session Duration",
        "Bounce Rate",
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    # Заполняем таблицу данными о ссылках
    for row, link_info in enumerate(campaign_info["links"], start=1):
        worksheet.write(row, 0, link_info["url"])
        worksheet.write(row, 1, link_info["campaign_content"])
        worksheet.write(row, 2, link_info["campaign_source"])
        worksheet.write(row, 3, link_info["campaign_medium"])
        worksheet.write(row, 4, link_info["short_id"])
        worksheet.write(row, 5, link_info["short_secure_url"])
        worksheet.write(row, 6, link_info["clicks_1d"])
        worksheet.write(row, 7, link_info["clicks_7d"])
        worksheet.write(row, 8, link_info["clicks_14d"])
        worksheet.write(row, 9, link_info["clicks_21d"])
        worksheet.write(row, 10, link_info["clicks_total"])
        worksheet.write(row, 11, link_info.get("ga_active_users", ""))
        worksheet.write(row, 12, link_info.get("ga_sessions", ""))
        worksheet.write(row, 13, link_info.get("ga_average_session_duration", ""))
        worksheet.write(row, 14, link_info.get("bounce_rate", ""))

        # Лист для данных о сессиях и датах
    worksheet_sessions = workbook.add_worksheet("Sessions and Dates")

    # Записываем заголовки для таблицы данных о сессиях и датах
    headers_sessions = ["Date", "Session Source/Medium", "Sessions", "Clicks"]
    for col, header in enumerate(headers_sessions):
        worksheet_sessions.write(0, col, header)

    # Заполняем таблицу данными о сессиях и датах
    for row, data in enumerate(graph_info["data"], start=1):
        worksheet_sessions.write(row, 0, data.get("date", ""))
        worksheet_sessions.write(row, 1, data.get("session_source_medium", ""))
        worksheet_sessions.write(row, 2, data.get("sessions", ""))
        worksheet_sessions.write(row, 3, data.get("clicks", ""))

    # Закрываем рабочую книгу
    workbook.close()
