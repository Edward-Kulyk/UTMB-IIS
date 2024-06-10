from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Campaign


def get_campaign_by_id(session: Session, campaign_id: int) -> Campaign | None:
    return session.execute(select(Campaign).where(Campaign.id == campaign_id)).scalar_one_or_none()


def get_campaign_list(session: Session, list_type: bool = None) -> Sequence[Campaign]:
    stmt = select(Campaign)

    if list_type is not None:
        stmt = stmt.where(Campaign.hide.is_(list_type))

    return session.execute(stmt).scalars().all()


def get_campaign_by_name(session: Session, campaign_name: str) -> Campaign | None:
    return session.execute(select(Campaign).where(Campaign.name == campaign_name)).scalar_one_or_none()
