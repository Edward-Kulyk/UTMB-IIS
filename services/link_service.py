from datetime import date, datetime
from typing import Any, Dict

from flask import jsonify
from sqlalchemy import Column, select

from crud import campaign_add, delete_link_db, get_default_values, update_link_db, utm_add_link, utm_check_exist
from database import get_db
from models import Campaign, UTMLink
from utils import create_short_link, delete_link_shot_io


def create_link(form_data: dict) -> tuple[str, Column[str]] | tuple[str, str]:
    url = form_data["url"]
    campaign_content = form_data.get("campaign_content", " ")
    campaign_source = form_data["campaign_source"]
    campaign_medium = form_data["campaign_medium"]
    campaign_name = form_data["campaign_name"]
    domain = form_data["domain"]
    slug = form_data.get("slug", "")

    new_link = UTMLink(
        url=url,
        campaign_content=campaign_content,
        campaign_source=campaign_source,
        campaign_medium=campaign_medium,
        campaign_name=campaign_name,
        domain=domain,
        slug=slug,
    )

    with get_db() as session:
        if utm_check_exist(session, new_link):
            error_message = "Link already exists"
            return error_message, ""

    utm_link = (
        f"{url}?utm_campaign={campaign_name.replace(' ', '+')}&utm_medium={campaign_medium.replace(' ', '+')}"
        f"&utm_source={campaign_source.replace(' ', '+')}&utm_content={campaign_content.replace(' ', '+')}"
    )
    short_url = create_short_link(domain, slug, utm_link)

    if short_url.get("error"):
        error_message = short_url["error"]
        return error_message, ""

    new_link.short_id = short_url["idString"]
    new_link.short_secure_url = short_url["secureShortURL"]

    if slug == "":
        new_link.slug = short_url["path"]

    short_secure_url = new_link.short_secure_url

    with get_db() as session:
        utm_add_link(session, new_link)

    return "", short_secure_url


def create_campaign(form_data) -> None:
    name = form_data["name"]
    url_by_default = form_data["url_by_default"]
    domain_by_default = form_data["domain_by_default"]
    start_date = datetime.strptime(form_data.get("start_date"), "%Y-%m-%d").date()

    # Validate start_date
    if not start_date:
        # Provide a default value or handle empty start_date based on your requirements
        start_date = date.today()  # Example: Use today's date as default

    new_campaign = Campaign(
        name=name,
        url_by_default=url_by_default,
        domain_by_default=domain_by_default,
        start_date=start_date,
        hide=False,  # Assuming hide is a boolean field
    )
    with get_db() as db:
        campaign_add(db, new_campaign)


def update_link(link_id: int, data: dict) -> Any | None:
    if link_id and data is not None:
        with get_db() as db:
            return update_link_db(db, link_id, data)
    return {"status": "error", "message": "Record not found"}


def delete_link(short_link_id: str):
    with get_db() as db:
        result = delete_link_db(db, short_link_id)
        if result == "Link not found":
            return jsonify({"status": "failure", "message": "Link not found"}), 404

    delete_link_shot_io(short_link_id)
    return jsonify({"status": "success", "message": "Record deleted successfully"})


def get_default_values_service(campaign_name: str) -> dict:
    with get_db() as db:
        campaign = get_default_values(db, campaign_name)
        if campaign:
            return {"url_by_default": campaign.url_by_default, "domain_by_default": campaign.domain_by_default}
        else:
            return {"error": "Campaign not found"}


def edit_campaign_row(campaign_id: int, data: Dict[str, str]) -> tuple[bool, str]:
    with get_db() as db:
        start_date_str = data.get("start_date")
        if start_date_str is not None:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = None
        hide = False if data["hide"].lower() == "false" else True

        stmt = select(Campaign).where(Campaign.id == campaign_id)
        campaign = db.execute(stmt).first()

        if not campaign:
            return False, "campaign not found"
        campaign.name = data["name"]
        campaign.url_by_default = data["url_by_default"]
        campaign.domain_by_default = data["domain_by_default"]
        campaign.start_date = start_date
        campaign.hide = hide

        db.commit()
        return True, "Row updated successfully"
