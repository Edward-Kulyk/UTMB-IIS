import re
from datetime import datetime
from io import BytesIO

from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

from config import Config
from database import get_session
from models import Blogger


def get_channel_video_views(api_key, channel_id):
    youtube = build("youtube", "v3", developerKey=api_key)

    # Получаем информацию о плейлисте "uploads" канала
    channel_info = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    uploads_playlist_id = channel_info["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Получаем список последних 10 видео канала
    playlist_items = (
        youtube.playlistItems().list(part="snippet", playlistId=uploads_playlist_id, maxResults=10).execute()
    )

    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_items["items"]]

    video_views = []
    # Получаем статистику для каждого видео
    for video_id in video_ids:
        video_response = youtube.videos().list(part="statistics", id=video_id).execute()
        views = int(video_response["items"][0]["statistics"]["viewCount"])
        video_views.append(views)

    return calculate_average_views(video_views)


# Функция для получения ID канала и сохранения его в базу данных
def get_and_save_channel_id(api_key, username, name):
    youtube = build("youtube", "v3", developerKey=api_key)

    # Получаем информацию о канале по имени пользователя
    channel_response = (
        youtube.search()
        .list(part="id", type="channel", maxResults=1, q=username)  # Параметр q для поиска по имени пользователя
        .execute()
    )
    if "items" not in channel_response or not channel_response["items"]:
        print("Канал с указанным именем пользователя не найден.")
        return None

    # Получаем ID канала
    channel_id = channel_response["items"][0]["id"]["channelId"]

    # Сохраняем информацию о блогере в базу данных
    blogger = Blogger(name=name, yt_channel_id=channel_id)
    with get_session() as session:
        session.add(blogger)
        session.session.commit()

    return channel_id


# Функция для расчета среднего количества просмотров
def calculate_average_views(views):
    if views:
        return sum(views) / len(views)
    else:
        return 0


def extract_username_from_url(channel_url):
    pattern = r"/@([A-Za-z0-9_\-]+)"
    match = re.search(pattern, channel_url)
    if match:
        return match.group(1)
    else:
        return None


def update_bloggers_avg():
    with get_session() as session:
        bloggers = session.execute(select(Blogger)).scalars().all()
        for blogger in bloggers:
            avg_views = get_channel_video_views(Config.api_key, blogger.yt_channel_id)
            blogger.yt_avg = avg_views
        session.commit()


def add_date_stamp_to_image(photo_stream, date_str, font_path="arial.ttf"):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    img = Image.open(photo_stream)
    if img.mode != "RGB":
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img)
    relative_font_size = int(min(img.size) / 20)
    font = ImageFont.truetype(font_path, relative_font_size)

    text = date.strftime("%Y-%m-%d")
    text_color = (255, 255, 255)  # White

    x_adjust = 40
    y_adjust = 20
    x = img.width - (relative_font_size * len(text) // 2) - x_adjust
    y = img.height - (relative_font_size * 2) - y_adjust

    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))  # Black shadow
    draw.text((x, y), text, font=font, fill=text_color)

    img_bytes = BytesIO()
    img.save(img_bytes, "JPEG")
    img_bytes.seek(0)

    return img_bytes


def get_bloggers():
    with get_session() as session:
        stmt = select(Blogger)
        return session.execute(stmt).scalars().all()
