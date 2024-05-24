from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Union

from sqlalchemy import Column, ColumnElement, Row, Select, and_, func, insert, select, tuple_, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import concat

from models import Campaign, ClicksDate, GoogleAnalyticsDataGraph, GoogleAnalyticsDataTable, UTMLink


def get_campaign_by_id(db: Session, campaign_id: Column[int] | int) -> Campaign | None:
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    return db.execute(stmt).scalar_one_or_none()


def get_campaign_links(db: Session, campaign_name: Column[str] | str) -> List[UTMLink] | Sequence[Any]:
    stmt: Select = select(UTMLink).where(UTMLink.campaign_name.is_(campaign_name))
    return db.execute(stmt).scalars().all()


def get_click_count(db: Session, link_id: Column[int] | int, start_date: Optional[ColumnElement[date] | date] = None,
                    end_date: Optional[ColumnElement[date] | None] = None) -> int:
    stmt = select(func.sum(ClicksDate.clicks_count)).where(ClicksDate.link_id == link_id)

    if start_date and end_date:
        stmt = stmt.where(and_(ClicksDate.date >= start_date, ClicksDate.date <= end_date))
    elif start_date:
        stmt = stmt.where(ClicksDate.date == start_date)

    return db.execute(stmt).scalar() or 0


def get_ga_data(
        db: Session, url: Column[str] | str, source_medium: Column[str] | str,
        content: Column[str] | str) -> Row[tuple[int, int, int, float]] | None:
    ga_data = (
        select(
            GoogleAnalyticsDataTable.active_users,
            GoogleAnalyticsDataTable.sessions,
            GoogleAnalyticsDataTable.average_session_duration,
            GoogleAnalyticsDataTable.bounce_rate,
        )
        .where(GoogleAnalyticsDataTable.url == url)
        .where(GoogleAnalyticsDataTable.session_source_medium == source_medium)
        .where(GoogleAnalyticsDataTable.content == content)
    )

    ga_result = db.execute(ga_data).one_or_none()

    return ga_result


def get_ga_data_other(db: Session, url: Column[str] | str, source_medium: list, content: list) -> Sequence[Row[tuple[str, str, int, int, int, float]]]:
    ga_data = (
        select(
            GoogleAnalyticsDataTable.content,
            GoogleAnalyticsDataTable.session_source_medium,
            GoogleAnalyticsDataTable.active_users,
            GoogleAnalyticsDataTable.sessions,
            GoogleAnalyticsDataTable.average_session_duration,
            GoogleAnalyticsDataTable.bounce_rate,
        )
        .where(GoogleAnalyticsDataTable.url == url)
        .where(GoogleAnalyticsDataTable.session_source_medium.notin_(source_medium))
        .where(GoogleAnalyticsDataTable.content.notin_(content))
    )

    ga_result = db.execute(ga_data).all()

    return ga_result


def get_graph_data(db: Session, campaign_name: Column[str] | str) -> Sequence[Row[Any]]:
    sub_query = (
        select(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url)
        .select_from(UTMLink)
        .where(UTMLink.campaign_name == campaign_name)
        .join(ClicksDate.link)
        .outerjoin(
            GoogleAnalyticsDataGraph,
            (
                    concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium)
                    == GoogleAnalyticsDataGraph.session_source_medium
            )
            & (UTMLink.url == GoogleAnalyticsDataGraph.url),
        )
        .group_by(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url)
        .order_by(func.sum(GoogleAnalyticsDataGraph.sessions).desc(), func.sum(ClicksDate.clicks_count).desc())
        .limit(5)
    )
    stmt = (
        select(
            concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium).label("source_medium"),
            ClicksDate.date,
            func.sum(ClicksDate.clicks_count).label("total_clicks"),
            func.sum(GoogleAnalyticsDataGraph.sessions).label("total_sessions"),
        )
        .select_from(UTMLink)
        .join(ClicksDate, UTMLink.id == ClicksDate.link_id)
        .outerjoin(
            GoogleAnalyticsDataGraph,
            and_(
                concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium)
                == GoogleAnalyticsDataGraph.session_source_medium,
                UTMLink.url == GoogleAnalyticsDataGraph.url,
                ClicksDate.date == GoogleAnalyticsDataGraph.date,
            ),
        )
        .where(tuple_(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url).in_(sub_query))
        .group_by(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url, ClicksDate.date)
        .order_by(UTMLink.campaign_source, UTMLink.campaign_medium, ClicksDate.date)
    )
    return db.execute(stmt).all()


def get_link(db: Session, link_id: Column[int] | int) -> UTMLink | None:
    stmt = select(UTMLink).where(UTMLink.id == link_id)
    return db.execute(stmt).scalar_one_or_none()


def insert_or_update_data(db: Session, model: Any, filters: Dict[str, Any], data: Dict[str, Any]) -> None:
    existing_record = db.execute(select(model).filter_by(**filters)).scalar_one_or_none()
    if existing_record:
        db.execute(update(model).where(model.id == existing_record.id).values(**data))
    else:
        db.execute(insert(model).values(**data))


def get_filtered_links(db: Session, form_data) -> Sequence[UTMLink]:
    stmt = select(UTMLink)
    filters = []
    # Создаем список фильтров, используя getlist для извлечения данных из формы
    if urls := form_data.getlist("url"):
        filters.append(UTMLink.url.in_(urls))
    if campaign_sources := form_data.getlist("campaign_source"):
        filters.append(UTMLink.campaign_source.in_(campaign_sources))
    if campaign_mediums := form_data.getlist("campaign_medium"):
        filters.append(UTMLink.campaign_medium.in_(campaign_mediums))
    if campaign_names := form_data.getlist("campaign_name"):
        filters.append(UTMLink.campaign_name.in_(campaign_names))
    if campaign_contents := form_data.getlist("campaign_content"):
        filters.append(UTMLink.campaign_content.in_(campaign_contents))

    # Применяем все фильтры, если они есть
    for filter_condition in filters:
        stmt = stmt.where(filter_condition)

    links = db.execute(stmt).scalars().all()
    return links
