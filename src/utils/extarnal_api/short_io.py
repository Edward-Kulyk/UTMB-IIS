import json
import time
from datetime import date

import requests

from src.database.models import UTMLink


class ShortLinkManager:
    def __init__(self, api_key):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": api_key,
        }

    def create_short_link(self, domain: str, slug: str, long_url: str):
        url = "https://api.short.io/links"
        data = {"originalURL": long_url, "domain": domain, "title": "ACCZ | API Created"}
        if slug:
            data["path"] = slug

        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        print(response.json())
        if response.status_code != 200:
            raise ValueError(f"Failed to create short link: {response.text}")
        return response.json()

    def get_clicks_filter(self, short_id: str, start_date: date, end_date: date):
        url = f"https://api-v2.short.io/statistics/link/{short_id}"
        querystring = {"period": "custom", "tz": "UTC", "startDate": start_date, "endDate": end_date}

        for attempt in range(8):
            try:
                response = requests.get(url, headers=self.headers, params=querystring)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    time.sleep(2**attempt)
                else:
                    raise ValueError(f"Failed to get statistic: {response.text}")
            except requests.RequestException:
                return None
        return None

    def edit_link(self, record: UTMLink):
        payload = json.dumps(
            {
                "allowDuplicates": False,
                "domain": record.domain,
                "path": record.slug,
                "originalURL": f"{record.url}?utm_campaign={record.campaign_name.replace(' ', '+')}&utm_medium={record.campaign_medium.replace(' ', '+')}&utm_source={record.campaign_source.replace(' ', '+')}&utm_content={record.campaign_content.replace(' ', '+')}",
            }
        )
        url = f"https://api.short.io/links/{record.short_id}"
        response = requests.post(url, headers=self.headers, data=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit link: {response.text}")
        return response

    def delete_link(self, link_id: str):
        url = f"https://api.short.io/links/{link_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to delete link: {response.text}")
        return response
