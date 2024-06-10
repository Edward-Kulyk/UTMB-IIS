from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import UTMLink


def get_all_links(
    session: Session,
) -> Sequence[UTMLink]:
    return session.execute(select(UTMLink)).scalars().all()


def get_link_by_id(session: Session, link_id: int) -> UTMLink | None:
    return session.execute(select(UTMLink).where(UTMLink.id == link_id)).scalar_one_or_none()


def get_links_by_campaign(session: Session, campaign_name: str) -> Sequence[UTMLink] | None:
    return session.execute(select(UTMLink).where(UTMLink.campaign_name == campaign_name)).scalars().all()


def save_link(session: Session, link: UTMLink) -> None:
    session.add(link)


def update_link(session: Session, link: UTMLink) -> None:
    pass


def delete_link(session: Session, link: UTMLink) -> None:
    session.delete(link)


def check_if_exist(
    session: Session,
    url: str,
    campaign_source: str,
    campaign_content: str,
    campaign_medium: str,
    campaign_name: str,
) -> bool:
    return (
        session.execute(
            select(UTMLink).where(
                UTMLink.url == url,
                UTMLink.campaign_content == campaign_content,
                UTMLink.campaign_source == campaign_source,
                UTMLink.campaign_medium == campaign_medium,
                UTMLink.campaign_name == campaign_name,
            )
        ).scalar_one_or_none()
        is not None
    )


def get_links_by_campaign_id(session: Session, campaign_id: int) -> Sequence[UTMLink]:
    return session.execute(select(UTMLink).where(UTMLink.campaign_name == campaign_id)).scalars().all()


def get_filtered_links(
    session: Session,
    urls: List[str] | None = None,
    campaign_sources: List[str] | None = None,
    campaign_mediums: List[str] | None = None,
    campaign_names: List[str] | None = None,
    campaign_contents: List[str] | None = None,
) -> Sequence[UTMLink]:
    stmt = select(UTMLink)
    filters = []

    if urls:
        filters.append(UTMLink.url.in_(urls))
    if campaign_sources:
        filters.append(UTMLink.campaign_source.in_(campaign_sources))
    if campaign_mediums:
        filters.append(UTMLink.campaign_medium.in_(campaign_mediums))
    if campaign_names:
        filters.append(UTMLink.campaign_name.in_(campaign_names))
    if campaign_contents:
        filters.append(UTMLink.campaign_content.in_(campaign_contents))

    for filter_condition in filters:
        stmt = stmt.where(filter_condition)

    return session.execute(stmt).scalars().all()
