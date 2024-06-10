from datetime import datetime
from typing import Any, Dict

from src.database.db import get_session
from src.repositories.campaign_repository import get_campaign_by_id, get_campaign_list, get_campaign_by_name


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


def edit_campaign_row(campaign_id: int, data: Dict[str, str]) -> tuple[bool, str]:
    with get_session() as session:
        start_date_str = data.get("start_date")
        if start_date_str is not None:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = None
        hide = False if data["hide"].lower() == "false" else True

        campaign = get_campaign_by_id(session, campaign_id)

        if not campaign:
            return False, "Campaign not found"

        campaign.name = data["name"]
        campaign.url_by_default = data["url_by_default"]
        campaign.domain_by_default = data["domain_by_default"]
        campaign.start_date = start_date
        campaign.hide = hide

        return True, "Row updated successfully"


def get_default_for_campaign(campaign_name: str) -> dict:
    with get_session() as session:
        campaign = get_campaign_by_name(session, campaign_name)
        if campaign:
            return {"url_by_default": campaign.url_by_default, "domain_by_default": campaign.domain_by_default}
        else:
            return {"error": "Campaign not found"}
