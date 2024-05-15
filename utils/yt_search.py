import re

from config import Config
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import db
from models import Blogger


def get_channel_video_views(api_key, channel_id):
    youtube = build("youtube", "v3", developerKey=api_key)
    try:
        # Получаем информацию о плейлисте "uploads" канала
        channel_info = (
            youtube.channels().list(part="contentDetails", id=channel_id).execute()
        )
        uploads_playlist_id = channel_info["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        # Получаем список последних 10 видео канала
        playlist_items = (
            youtube.playlistItems()
            .list(part="snippet", playlistId=uploads_playlist_id, maxResults=10)
            .execute()
        )

        video_ids = [
            item["snippet"]["resourceId"]["videoId"] for item in playlist_items["items"]
        ]

        video_views = []
        # Получаем статистику для каждого видео
        for video_id in video_ids:
            video_response = (
                youtube.videos().list(part="statistics", id=video_id).execute()
            )
            views = int(video_response["items"][0]["statistics"]["viewCount"])
            video_views.append(views)

        return calculate_average_views(video_views)

    except HttpError as e:
        print(f"Произошла ошибка HTTP {e.resp.status}: {e.content}")
        return None


# Функция для получения ID канала и сохранения его в базу данных
def get_and_save_channel_id(api_key, username, name):
    youtube = build("youtube", "v3", developerKey=api_key)
    try:
        # Получаем информацию о канале по имени пользователя
        channel_response = (
            youtube.search()
            .list(
                part="id",
                type="channel",
                maxResults=1,
                q=username,  # Параметр q для поиска по имени пользователя
            )
            .execute()
        )
        if "items" not in channel_response or not channel_response["items"]:
            print("Канал с указанным именем пользователя не найден.")
            return None

        # Получаем ID канала
        channel_id = channel_response["items"][0]["id"]["channelId"]

        # Сохраняем информацию о блогере в базу данных
        blogger = Blogger(name=name, yt_channel_id=channel_id)
        db.session.add(blogger)
        db.session.commit()

        return channel_id

    except HttpError as e:
        print(f"Произошла ошибка HTTP {e.resp.status}: {e.content}")
        return None


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
    bloggers = Blogger.query.all()
    for blogger in bloggers:
        avg_views = get_channel_video_views(Config.api_key, blogger.yt_channel_id)
        print(avg_views)
        blogger.yt_avg = avg_views
    db.session.commit()
