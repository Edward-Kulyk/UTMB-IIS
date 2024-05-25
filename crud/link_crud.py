from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Column, not_, select
from sqlalchemy.orm import Session

from models import Campaign, ClicksDate, UTMLink


def utm_check_exist(session: Session, new_link: UTMLink) -> bool:
    stmt = select(UTMLink).where(
        UTMLink.url == new_link.url,
        UTMLink.campaign_content == new_link.campaign_content,
        UTMLink.campaign_source == new_link.campaign_source,
        UTMLink.campaign_medium == new_link.campaign_medium,
        UTMLink.campaign_name == new_link.campaign_name,
        UTMLink.domain == new_link.domain,
        UTMLink.slug == new_link.slug,
    )
    return session.execute(stmt).scalar_one_or_none() is not None


def utm_add_link(session: Session, new_link: UTMLink) -> None:
    session.add(new_link)
    session.commit()


def campaign_add(session: Session, new_campaign: Campaign) -> None:
    session.add(new_campaign)
    session.commit()


def get_campaign_list(session: Session, list_type: bool = None) -> Sequence[Campaign]:
    """
    Retrieve a list of campaigns from the database based on their visibility status.

    Args:
        session (Session): The database session to use for querying.
        list_type (bool): The type of campaigns to retrieve. Acceptable values are:
            - True: Retrieve only the hidden campaigns.
            - False: Retrieve only the visible campaigns.
            - None: Retrieve all campaigns, regardless of their visibility status.

    Returns:
        list: A list of Campaign objects matching the specified visibility status.
    """
    stmt = select(Campaign)

    if list_type is not None:
        stmt = stmt.where(Campaign.hide.is_(list_type))

    campaigns = session.execute(stmt).scalars().all()
    return campaigns


def update_link_db(session: Session, link_id: int | Column[int], data: dict) -> dict[Any, Any]:
    record = session.execute(select(UTMLink).filter_by(short_id=link_id)).scalar_one_or_none()
    if record:
        record.campaign_source = data["campaign_source"]
        record.campaign_medium = data["campaign_medium"]
        record.campaign_content = data["campaign_content"]
        session.commit()
        return {"status": "success", "message": "Record updated successfully"}
    else:
        return {"status": "error", "message": "Record not found"}


def delete_link_db(session: Session, short_id: str) -> str:
    stmt = select(UTMLink).where(UTMLink.short_id == short_id)
    link = session.execute(stmt).scalar_one_or_none()
    if link:
        session.delete(link)
        session.commit()
        return "Success"
    else:
        return "Link not found"


def get_default_values(session: Session, campaign_name: str) -> Campaign | None:
    stmt = select(Campaign).where(Campaign.name == campaign_name)
    campaign = session.execute(stmt).scalar_one_or_none()
    return campaign


def get_utm_links(session: Session):
    stmt = select(UTMLink).join(Campaign, UTMLink.campaign_name == Campaign.name).where(not_(Campaign.hide))
    return session.execute(stmt).scalars().all()


def get_clicks_date(session: Session, link_id: int, click_date: datetime):
    stmt = select(ClicksDate).where(ClicksDate.link_id == link_id).where(ClicksDate.date == click_date)
    return session.execute(stmt).scalar_one_or_none()


def update_clicks_date(session: Session, link_click_date: ClicksDate, new_clicks_count: Column[int]) -> None:
    link_click_date.clicks_count = new_clicks_count
    session.commit()


def add_clicks_date(session: Session, link_id: int, click_date: datetime, clicks_count: int):
    link_click_date = ClicksDate(link_id=link_id, date=click_date, clicks_count=clicks_count)
    session.add(link_click_date)
    session.commit()
