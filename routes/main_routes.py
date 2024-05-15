import json
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse

import pandas as pd
from config import Config
from flask import (Blueprint, jsonify, redirect, render_template, request,
                   send_file, session)
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google_auth_oauthlib.flow import Flow
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import func

from app import db
from models import (Blogger, Campaign, ClicksDate, ExcludedOption,
                    GoogleAnalyticsDataGraph, GoogleAnalyticsDataTable,
                    UTMLink)
from utils.db_utils import (generate_campaign_excel, get_campaign_info,
                            get_graph_info)
from utils.ga4_requests import (build_analytics_request_graph,
                                build_analytics_request_table)
from utils.short_link import (create_short_link, delete_link, edit_link,
                              update_clicks_count)
from utils.uniq_values import unique_list_tags
from utils.yt_search import get_and_save_channel_id, update_bloggers_avg

main = Blueprint(
    "main",
    __name__,
)


@main.route("/", methods=["GET", "POST"])
def index():
    short_secure_url = None
    error_message = None

    (
        unique_url,
        unique_campaign_content,
        unique_campaign_source,
        unique_campaign_medium,
        unique_campaign_name,
    ) = unique_list_tags()

    if request.method == "POST":
        url = request.form["url"]
        campaign_content = request.form.get("campaign_content", " ")
        campaign_source = request.form["campaign_source"]
        campaign_medium = request.form["campaign_medium"]
        campaign_name = request.form["campaign_name"]
        domain = request.form["domain"]
        slug = request.form.get("slug", "")
        print(request.environ.get("REMOTE_USER"))
        if url == "other":
            url = request.form["url_other"]
        if campaign_content == "other":
            campaign_content = request.form["campaign_content_other"]
        if campaign_source == "other":
            campaign_source = request.form["campaign_source_other"]
        if campaign_medium == "other":
            campaign_medium = request.form["campaign_medium_other"]
        if campaign_name == "other":
            campaign_name = request.form["campaign_name_other"]

        # Construct the UTM link with spaces replaced by '+'
        utm_link = f"{url}?utm_campaign={campaign_name.replace(' ', '+')}&utm_medium={campaign_medium.replace(' ', '+')}&utm_source={campaign_source.replace(' ', '+')}&utm_content={campaign_content.replace(' ', '+')}"

        # Check if a similar record already exists
        existing_record = UTMLink.query.filter_by(
            url=url,
            campaign_content=campaign_content,
            campaign_source=campaign_source,
            campaign_medium=campaign_medium,
            campaign_name=campaign_name,
            domain=domain,
            slug=slug,
        ).first()

        if existing_record:
            error_message = "Similar record already exists."
        else:

            # Create UTM link using Short.io API
            short_url = create_short_link(domain, slug, utm_link)

            if short_url.get("error"):
                # Handle error case (e.g., log the error, display an error message)
                error_message = short_url["error"]

            else:
                # Update the database with short link information
                short_id = short_url["idString"]
                short_secure_url = short_url["secureShortURL"]
                if slug == "":
                    slug = short_url["path"]
                # Save data to the database
                utm_link = UTMLink(
                    url=url,
                    campaign_content=campaign_content,
                    campaign_source=campaign_source,
                    campaign_medium=campaign_medium,
                    campaign_name=campaign_name,
                    domain=domain,
                    slug=slug,
                    short_id=short_id,
                    short_secure_url=short_secure_url,
                )
                db.session.add(utm_link)
                db.session.commit()

    if short_secure_url is None:
        return render_template(
            "index.html",
            unique_campaign_contents=unique_campaign_content,
            unique_campaign_sources=unique_campaign_source,
            unique_campaign_mediums=unique_campaign_medium,
            unique_campaign_names=unique_campaign_name,
            unique_url=unique_url,
            error_message=error_message,
        )
    else:
        return render_template(
            "index.html",
            unique_campaign_contents=unique_campaign_content,
            unique_campaign_sources=unique_campaign_source,
            unique_campaign_mediums=unique_campaign_medium,
            unique_campaign_names=unique_campaign_name,
            unique_url=unique_url,
            short_url=short_secure_url,
            error_message=error_message,
        )


@main.route("/exclude-options", methods=["GET", "POST"])
def exclude_options():
    if request.method == "POST":
        for field_name, values in request.form.lists():
            if field_name.startswith("exclude_"):
                option_type = field_name.replace("exclude_", "")
                for value in values:
                    excluded_option = ExcludedOption(
                        option_type=option_type, option_value=value
                    )
                    db.session.add(excluded_option)

        db.session.commit()

    (
        unique_url,
        unique_campaign_content,
        unique_campaign_source,
        unique_campaign_medium,
        unique_campaign_name,
    ) = unique_list_tags()

    return render_template(
        "exclude_options.html",
        unique_campaign_contents=unique_campaign_content,
        unique_campaign_sources=unique_campaign_source,
        unique_campaign_mediums=unique_campaign_medium,
        unique_campaign_names=unique_campaign_name,
        unique_urls=unique_url,
    )


@main.route("/manage-exclusions", methods=["GET", "POST"])
def manage_exclusions():
    if request.method == "POST":
        for field_name in request.form:
            if field_name.startswith("include_"):
                option_type = field_name.replace("include_", "")
                included_values = request.form.getlist(field_name)
                for value in included_values:
                    ExcludedOption.query.filter_by(
                        option_type=option_type, option_value=value
                    ).delete()
        db.session.commit()
    excluded_campaign_sources = (
        ExcludedOption.query.filter(ExcludedOption.option_type == "campaign_sources[]")
        .distinct()
        .all()
    )
    excluded_campaign_mediums = (
        ExcludedOption.query.filter(ExcludedOption.option_type == "campaign_mediums[]")
        .distinct()
        .all()
    )
    excluded_campaign_contents = (
        ExcludedOption.query.filter(ExcludedOption.option_type == "campaign_contents[]")
        .distinct()
        .all()
    )
    excluded_campaign_names = (
        ExcludedOption.query.filter(ExcludedOption.option_type == "campaign_names[]")
        .distinct()
        .all()
    )
    excluded_urls = (
        ExcludedOption.query.filter(ExcludedOption.option_type == "urls[]")
        .distinct()
        .all()
    )

    return render_template(
        "manage_exclusions.html",
        excluded_campaign_contents=excluded_campaign_contents,
        excluded_campaign_sources=excluded_campaign_sources,
        excluded_campaign_mediums=excluded_campaign_mediums,
        excluded_campaign_names=excluded_campaign_names,
        excluded_urls=excluded_urls,
    )


@main.route("/campaigns", methods=["GET"])
def campaigns():
    # Получаем все кампании, у которых hide равно False
    campaigns = Campaign.query.filter_by(hide=False).all()

    # Собираем информацию о кампаниях, связанных с ними ссылках и кликах в один объект
    aggregate_campaigns = []
    all_sessions_and_dates = []

    for campaign in campaigns:
        campaign_info = get_campaign_info(campaign)
        aggregate_campaigns.append(campaign_info)

        campaign_data = get_graph_info(campaign)

        # Сортировка данных по дате и источнику/среде
        campaign_data["data"] = sorted(
            campaign_data["data"], key=lambda x: (x["session_source_medium"], x["date"])
        )

        # Добавление структуры кампании в общий список
        all_sessions_and_dates.append(campaign_data)
    return render_template(
        "campaigns.html",
        aggregate_campaign_data=aggregate_campaigns,
        graph_data=json.dumps(all_sessions_and_dates, ensure_ascii=False, default=str),
    )


@main.route("/import", methods=["GET"])
def import_excel_data():
    # Read Excel file into a pandas DataFrame
    df = pd.read_excel("Link.xlsx")

    # Iterate through DataFrame rows and add to the database
    for index, row in df.iterrows():
        utm_link = UTMLink(
            url=row["url"],
            campaign_content=row["campaign_content"],
            campaign_source=row["campaign_source"],
            campaign_medium=row["campaign_medium"],
            campaign_name=row["campaign_name"],
            domain=row["domain"],
            slug=row["slug"],
            short_id=row["short_id"],
            short_secure_url=row["short_secure_url"],
            clicks_count=row["clicks_count"],
            clicks_count24h=row["clicks_count24h"],
            clicks_count1w=row["clicks_count1w"],
            clicks_count2w=row["clicks_count2w"],
            clicks_count3w=row["clicks_count3w"],
        )
        db.session.add(utm_link)

    # Commit changes to the database
    db.session.commit()
    return "Import success"


@main.route("/filter_setting", methods=["GET", "POST"])
def filter_setting():
    if request.method == "POST":
        # Извлечение данных из формы
        start_date = request.form.get("date_from")
        end_date = request.form.get("date_to")
        url = request.form.getlist(
            "url"
        )  # `getlist` для получения всех выбранных значений
        campaign_source = request.form.getlist("campaign_source")
        campaign_medium = request.form.getlist("campaign_medium")
        campaign_name = request.form.getlist("campaign_name")
        campaign_content = request.form.getlist("campaign_content")
        # Фильтрация данных в базе данных по полученным параметрам
        query = UTMLink.query
        if url:
            query = query.filter(UTMLink.url.in_(url))
        if campaign_source:
            query = query.filter(UTMLink.campaign_source.in_(campaign_source))
        if campaign_medium:
            query = query.filter(UTMLink.campaign_medium.in_(campaign_medium))
        if campaign_name:
            query = query.filter(UTMLink.campaign_name.in_(campaign_name))
        if campaign_content:
            query = query.filter(UTMLink.campaign_content.in_(campaign_content))

        links_data = []
        links = query.all()
        for link in links:
            clicks = (
                ClicksDate.query.with_entities(func.sum(ClicksDate.clicks_count))
                .filter(
                    ClicksDate.link_id == link.id,
                    ClicksDate.date >= start_date,
                    ClicksDate.date <= end_date,
                )
                .scalar()
                or 0
            )

            source_medium = f"{link.campaign_source} / {link.campaign_medium}"

            sessions, users = GoogleAnalyticsDataGraph.query.with_entities(
                func.sum(GoogleAnalyticsDataGraph.sessions),
                func.sum(GoogleAnalyticsDataGraph.active_users),
            ).filter(
                GoogleAnalyticsDataGraph.date >= start_date,
                GoogleAnalyticsDataGraph.date <= end_date,
                GoogleAnalyticsDataGraph.url == link.url,
                GoogleAnalyticsDataGraph.session_source_medium == source_medium,
            ).first() or (
                0,
                0,
            )

            print(sessions, users)
            link_data = {
                "url": link.url,
                "campaign_source": link.campaign_source,
                "campaign_medium": link.campaign_medium,
                "campaign_name": link.campaign_name,
                "campaign_content": link.campaign_content,
                "clicks": clicks,
                "sessions": sessions,
                "users": users,
            }
            links_data.append(link_data)

        return render_template("filtered_utm.html", link_info=links_data)

    if request.method == "GET":
        # Query to get all unique campaign contents
        unique_campaign_contents = (
            UTMLink.query.with_entities(UTMLink.campaign_content).distinct().all()
        )

        # Query to get all unique campaign sources
        unique_campaign_sources = (
            UTMLink.query.with_entities(UTMLink.campaign_source).distinct().all()
        )

        # Query to get all unique campaign mediums
        unique_campaign_mediums = (
            UTMLink.query.with_entities(UTMLink.campaign_medium).distinct().all()
        )

        # Query to get all unique campaign names
        unique_campaign_names = (
            UTMLink.query.with_entities(UTMLink.campaign_name).distinct().all()
        )

        # Query to get all unique URLs
        unique_urls = UTMLink.query.with_entities(UTMLink.url).distinct().all()

        return render_template(
            "filter_setting.html",
            unique_campaign_contents=unique_campaign_contents,
            unique_campaign_sources=unique_campaign_sources,
            unique_campaign_mediums=unique_campaign_mediums,
            unique_campaign_names=unique_campaign_names,
            unique_url=unique_urls,
        )


@main.route("/update-clicks", methods=["GET"])
def update_clicks():
    update_clicks_count()
    update_bloggers_avg()
    return redirect("/campaigns")


@main.route("/edit-row/<string:id>", methods=["POST"])
def edit_record(id):
    data = request.json
    record = UTMLink.query.filter_by(short_id=str(id)).first()
    if record:
        record.campaign_source = data["campaign_source"]
        record.campaign_medium = data["campaign_medium"]
        record.campaign_content = data.get(
            "campaign_content"
        )  # Используйте .get для необязательных полей
        db.session.commit()
        edit_link(record.id)
        return jsonify({"status": "success", "message": "Record updated successfully"})
    else:
        return jsonify({"status": "error", "message": "Record not found"})


@main.route("/delete-row/<string:id>", methods=["POST"])
def delete_record(id):
    record = UTMLink.query.filter_by(short_id=str(id)).first()
    if record:
        delete_link(record.short_id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({"status": "success", "message": "Record deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Record not found"})


@main.route("/data-stamp", methods=["GET"])
def data_stamp():
    return render_template("data-stamp.html")


@main.route("/add_data_stamp", methods=["POST"])
def add_data_stamp():
    photo = request.files["photo"]
    date_str = request.form["date"]
    date = datetime.strptime(date_str, "%Y-%m-%d")

    img = Image.open(photo.stream)
    if img.mode != "RGB":
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    # Using a relative font size based on the image height, ensuring it's readable
    relative_font_size = int(min(img.size) / 20)
    font_path = "arial.ttf"  # Make sure this path is correct for your setup
    font = ImageFont.truetype(font_path, relative_font_size)

    text = date.strftime("%Y-%m-%d")
    text_color = (255, 255, 255)  # White

    # Adjust text positioning a bit higher and to the right
    x_adjust = 40  # Increase for further right
    y_adjust = 20  # Increase for higher
    x = img.width - (relative_font_size * len(text) // 2) - x_adjust
    y = img.height - (relative_font_size * 2) - y_adjust

    # Adding a simple shadow for legibility
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))  # Black shadow
    draw.text((x, y), text, font=font, fill=text_color)

    img_bytes = BytesIO()
    img.save(img_bytes, "JPEG")  # Ensure to save as RGB for JPEG
    img_bytes.seek(0)

    return send_file(
        img_bytes,
        mimetype="image/jpeg",
        as_attachment=True,
        download_name="modified_image.jpg",
    )


@main.route("/add_campaign", methods=["GET", "POST"])
def add_campaign():
    if request.method == "POST":
        name = request.form["name"]
        url_by_default = request.form["url_by_default"]
        domain_by_default = request.form["domain_by_default"]
        start_date = datetime.strptime(
            request.form.get("start_date"), "%Y-%m-%d"
        ).date()

        # Validate start_date
        if not start_date:
            # Provide a default value or handle empty start_date based on your requirements
            start_date = datetime.date.today()  # Example: Use today's date as default

        campaign = Campaign(
            name=name,
            url_by_default=url_by_default,
            domain_by_default=domain_by_default,
            start_date=start_date,
            hide=False,  # Assuming hide is a boolean field
        )

        db.session.add(campaign)
        db.session.commit()

        return render_template("campaign_creation.html")

    return render_template("campaign_creation.html")


@main.route("/get_default_values", methods=["POST"])
def get_default_values():
    campaign_name = request.json["campaign_name"]
    default_values = Campaign.query.filter_by(name=campaign_name).first()
    print(campaign_name)
    return jsonify(
        {
            "url_by_default": default_values.url_by_default,
            "domain_by_default": default_values.domain_by_default,
        }
    )


@main.route("/edit_campaing_name_list", methods=["GET"])
def edit_campaing_name_list():
    campaigns = Campaign.query.all()
    return render_template("campaign_name_list.html", campaigns=campaigns)


@main.route("/edit-campaign-row/<int:id>", methods=["POST"])
def edit_row(id):
    # Получаем данные из запроса
    data = request.json
    start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d").date()
    data["hide"] = False if data["hide"].lower() == "false" else True
    # Находим запись в базе данных по переданному id
    campaign = Campaign.query.get(id)

    # Обновляем данные кампании
    campaign.name = data["name"]
    campaign.url_by_default = data["url_by_default"]
    campaign.domain_by_default = data["domain_by_default"]
    campaign.start_date = start_date
    campaign.hide = data["hide"]

    # Сохраняем изменения
    db.session.commit()

    # Отправляем ответ клиенту
    return jsonify({"status": "success", "message": "Row updated successfully"})


@main.route("/query", methods=["POST", "GET"])
def query():
    if request.method == "POST":
        campaign = request.form.get("campaign_name_query", "")
        campaign_object = Campaign.query.filter(Campaign.name == campaign).first()
        # Здесь вызывается ваша функция для создания данных кампании
        campaign_info = get_campaign_info(campaign_object)
        graph_info = get_graph_info(campaign_object)
        # Создаем буфер в памяти для хранения данных Excel
        output = BytesIO()

        # Создаем Excel-файл в буфере
        generate_campaign_excel(campaign_info, graph_info, output)

        # Возвращаем буфер в начало перед отправкой
        output.seek(0)

        # Отправляем файл пользователю
        return send_file(output, as_attachment=True, download_name=f"{campaign}.xlsx")
    list_names = []
    if request.method == "GET":
        campaign_names = Campaign.query.filter(Campaign.hide == False).all()
        for campaign in campaign_names:
            list_names.append(campaign.name)
        return render_template("campaign_query.html", campaign_names=list_names)


# Инициализация объекта Flow для OAuth 2.0
flow = Flow.from_client_secrets_file(
    "creditals.json",
    scopes=[
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/cloud-platform",  # Добавьте это разрешение для доступа к Google Cloud API
    ],
    redirect_uri="http://127.0.0.1/callback",
)


@main.route("/GA4")
def index2():
    authorization_url, state = flow.authorization_url()

    session["state"] = state
    return redirect(authorization_url)


@main.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    return redirect("http://127.0.0.1/analytics")


@main.route("/analytics")
def analytics_data():
    # Получаем учетные данные из сессии
    creds = flow.credentials

    # Создаем клиента BetaAnalyticsDataClient с использованием учетных данных
    client = BetaAnalyticsDataClient(credentials=creds)

    # Получаем список всех кампаний
    campaigns = Campaign.query.filter(Campaign.hide == False).all()

    for campaign in campaigns:
        for property_id in Config.PROPERTY_IDS:
            start_date = campaign.start_date - timedelta(weeks=2)
            end_date = campaign.start_date + timedelta(weeks=3)

            parsed_url = urlparse(campaign.url_by_default)
            path = parsed_url.path
            path = path[:-1]
            # Создаем запрос с фильтром
            request = build_analytics_request_graph(
                property_id, path, start_date, end_date
            )

            # Выполняем запрос к Google Analytics
            response = client.run_report(request)

            data_to_insert = []
            # Group data
            for row in response.rows:
                date = datetime.strptime(row.dimension_values[0].value, "%Y%m%d")
                session_source_medium = row.dimension_values[1].value
                url = campaign.url_by_default
                active_users = row.metric_values[0].value
                sessions = row.metric_values[1].value
                content = row.dimension_values[2].value

                data_to_insert.append(
                    {
                        "session_source_medium": session_source_medium,
                        "url": url,
                        "active_users": active_users,
                        "date": date,
                        "sessions": sessions,
                        "content": content,
                    }
                )

            # Check and insert/update records
            for data in data_to_insert:
                # Check if the record already exists
                existing_record = GoogleAnalyticsDataGraph.query.filter_by(
                    session_source_medium=data["session_source_medium"],
                    url=data["url"],
                    date=data["date"].date(),
                ).first()
                if existing_record:
                    # Update existing record
                    existing_record.active_users = data["active_users"]
                    existing_record.sessions = data["sessions"]
                else:
                    # Add new record
                    google_analytics_data = GoogleAnalyticsDataGraph(**data)
                    db.session.add(google_analytics_data)

            # Commit changes
            db.session.commit()

            # Создаем запрос с фильтром
            request = build_analytics_request_table(
                property_id, path, start_date, end_date
            )

            # Выполняем запрос к Google Analytics
            response = client.run_report(request)

            data_to_insert = []
            for row in response.rows:
                session_source_medium = row.dimension_values[0].value
                content = row.dimension_values[2].value
                url = campaign.url_by_default
                active_users = row.metric_values[0].value
                average_session_duration = row.metric_values[1].value
                bounce_rate = row.metric_values[2].value
                sessions = row.metric_values[3].value

                # Check if the record already exists
                existing_record = GoogleAnalyticsDataTable.query.filter_by(
                    session_source_medium=session_source_medium,
                    url=url,
                    content=content,
                ).first()
                if existing_record:
                    # Update existing record
                    existing_record.active_users = active_users
                    existing_record.average_session_duration = average_session_duration
                    existing_record.bounce_rate = bounce_rate
                    existing_record.sessions = sessions
                else:
                    # Add new record
                    data_to_insert.append(
                        {
                            "session_source_medium": session_source_medium,
                            "url": url,
                            "active_users": active_users,
                            "average_session_duration": average_session_duration,
                            "bounce_rate": bounce_rate,
                            "sessions": sessions,
                            "content": content,
                        }
                    )

            # Commit changes
            for data in data_to_insert:
                google_analytics_data = GoogleAnalyticsDataTable(**data)
                db.session.add(google_analytics_data)
            db.session.commit()

    # Возвращаем HTML-таблицу в качестве результата
    return "Data has been fetched and stored to the database."


@main.route("/bloggers", methods=["GET", "POST"])
def bloggers_page():
    bloggers = Blogger.query.all()
    if request.method == "POST":
        name = request.form["social_name"]
        yt_name = request.form.get("yt_name", False)
        if yt_name:
            get_and_save_channel_id(Config.api_key, yt_name, name)
            update_bloggers_avg()
            return render_template(
                "new_observ.html", error_message="Added", bloggers=bloggers
            )
        else:
            return render_template(
                "new_observ.html", error_message="NOT found", bloggers=bloggers
            )

    if request.method == "GET":
        return render_template("new_observ.html", bloggers=bloggers)
