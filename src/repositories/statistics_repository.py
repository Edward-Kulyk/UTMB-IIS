from datetime import date
from typing import Any, Sequence

from sqlalchemy import Column, Row, and_, func, select, tuple_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import concat

from src.database.models import ClicksDate, GoogleAnalyticsDataGraph, GoogleAnalyticsDataTable, UTMLink


def get_click_count(
    session: Session,
    link_id: int,
    start_date: date = None,
    end_date: date = None,
) -> int:
    stmt = select(func.sum(ClicksDate.clicks_count)).where(ClicksDate.link_id == link_id)

    if start_date and end_date:
        stmt = stmt.where(and_(ClicksDate.date >= start_date, ClicksDate.date <= end_date))
    elif start_date:
        stmt = stmt.where(ClicksDate.date == start_date)

    return session.execute(stmt).scalar() or 0


def get_ga_data(
    session: Session, url: Column[str] | str, source_medium: Column[str] | str, content: None | Column[str]
) -> GoogleAnalyticsDataTable | None:
    return session.execute(
        select(GoogleAnalyticsDataTable)
        .where(GoogleAnalyticsDataTable.url == url)
        .where(GoogleAnalyticsDataTable.session_source_medium == source_medium)
        .where(GoogleAnalyticsDataTable.content == content)
    ).scalar_one_or_none()


def get_ga_data_other(
    session: Session, url: Column[str] | str, source_medium: list, content: list
) -> Sequence[Row[tuple[str, str, int, int, int, float]]]:
    return session.execute(
        select(
            GoogleAnalyticsDataTable.content,
            GoogleAnalyticsDataTable.session_source_medium,
            GoogleAnalyticsDataTable.active_users,
            GoogleAnalyticsDataTable.sessions,
            GoogleAnalyticsDataTable.average_session_duration,
            GoogleAnalyticsDataTable.bounce_rate,
        ).where(
            GoogleAnalyticsDataTable.url == url,
            GoogleAnalyticsDataTable.session_source_medium.notin_(source_medium),
            GoogleAnalyticsDataTable.content.notin_(content),
        )
    ).all()


def get_graph_data(session: Session, campaign_name: Column[str] | str) -> Sequence[Row[Any]]:
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
    return session.execute(stmt).all()
