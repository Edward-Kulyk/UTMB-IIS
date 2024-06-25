from datetime import date
from typing import Any, Sequence, Dict

from sqlalchemy import Column, Row, and_, func, select, tuple_, insert, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import concat

from src.database.models import ClicksDate, GoogleAnalyticsData, UTMLink


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


def get_ga_data(session: Session, url, source_medium, content, start_date, end_date):
    # Perform the query
    return session.execute(
        select(
            func.sum(GoogleAnalyticsData.active_users).label('active_users'),
            func.sum(GoogleAnalyticsData.sessions).label('sessions'),
            (func.sum(GoogleAnalyticsData.sessions * GoogleAnalyticsData.average_session_duration) /
             func.coalesce(func.sum(GoogleAnalyticsData.sessions), 1)).label('average_session_duration') / 100,
            (func.sum(GoogleAnalyticsData.sessions * GoogleAnalyticsData.bounce_rate) /
             func.coalesce(func.sum(GoogleAnalyticsData.sessions), 1)).label('bounce_rate')
        ).where(
            and_(
                GoogleAnalyticsData.url == url,
                GoogleAnalyticsData.session_source_medium == source_medium,
                GoogleAnalyticsData.content == content,
                GoogleAnalyticsData.date >= start_date,
                GoogleAnalyticsData.date <= end_date
            )
        ).group_by(GoogleAnalyticsData.session_source_medium, GoogleAnalyticsData.url)
    ).all()


def get_ga_data_other(session: Session, url: Column[str] | str, source_medium: list, content: list, start_date,
                      end_date):
    return session.execute(
        select(
            GoogleAnalyticsData.session_source_medium,

            GoogleAnalyticsData.url,

            GoogleAnalyticsData.content,

            func.sum(GoogleAnalyticsData.active_users).label('active_users'),

            func.sum(GoogleAnalyticsData.sessions).label('sessions'),

            (func.sum(GoogleAnalyticsData.sessions * GoogleAnalyticsData.average_session_duration) /
             func.coalesce(func.sum(GoogleAnalyticsData.sessions), 1)).label('average_session_duration') / 100,

            (func.sum(GoogleAnalyticsData.sessions * GoogleAnalyticsData.bounce_rate) /
             func.coalesce(func.sum(GoogleAnalyticsData.sessions), 1)).label('bounce_rate')

        ).where(
            GoogleAnalyticsData.url == url,
            GoogleAnalyticsData.session_source_medium.notin_(source_medium),
            GoogleAnalyticsData.content.notin_(content),
            GoogleAnalyticsData.date >= start_date,
            GoogleAnalyticsData.date <= end_date,
        ).group_by(GoogleAnalyticsData.session_source_medium,
                   GoogleAnalyticsData.url,
                   GoogleAnalyticsData.content)
    ).all()


def get_graph_data(session: Session, campaign_name: Column[str] | str, start_date, end_date) -> Sequence[Row[Any]]:
    sub_query = (
        select(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url)
        .select_from(UTMLink)
        .join(ClicksDate.link)
        .outerjoin(
            GoogleAnalyticsData,
            (concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium) == GoogleAnalyticsData.session_source_medium)
            & (UTMLink.url == GoogleAnalyticsData.url),
        )
        .group_by(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url)
        .where(UTMLink.campaign_name == campaign_name,
               ClicksDate.date >= start_date,
               ClicksDate.date <= end_date,
               GoogleAnalyticsData.date >= start_date,
               GoogleAnalyticsData.date <= end_date)
        .order_by(func.sum(GoogleAnalyticsData.sessions).desc(), func.sum(ClicksDate.clicks_count).desc())
        .limit(5)
    )
    stmt = (
        select(
            concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium).label("source_medium"),
            ClicksDate.date,
            func.sum(ClicksDate.clicks_count).label("total_clicks"),
            func.sum(GoogleAnalyticsData.sessions).label("total_sessions"),
        )
        .select_from(UTMLink)
        .join(ClicksDate, UTMLink.id == ClicksDate.link_id)
        .outerjoin(
            GoogleAnalyticsData,
            and_(
                concat(UTMLink.campaign_source, " / ", UTMLink.campaign_medium)
                == GoogleAnalyticsData.session_source_medium,
                UTMLink.url == GoogleAnalyticsData.url,
                ClicksDate.date == GoogleAnalyticsData.date,
            ),
        )
        .where(tuple_(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url).in_(sub_query),
               ClicksDate.date >= start_date,
               ClicksDate.date <= end_date,
               GoogleAnalyticsData.date >= start_date,
               GoogleAnalyticsData.date <= end_date
               )
        .group_by(UTMLink.campaign_source, UTMLink.campaign_medium, UTMLink.url, ClicksDate.date)
        .order_by(UTMLink.campaign_source, UTMLink.campaign_medium, ClicksDate.date)
    )
    return session.execute(stmt).all()


def insert_or_update_data(session: Session, model: GoogleAnalyticsData, filters: Dict[str, Any],
                          data: Dict[str, Any]) -> None:
    existing_record = session.execute(select(model).filter_by(**filters)).scalar_one_or_none()
    if existing_record:
        if data["sessions"] > existing_record.sessions:
            session.execute(update(model).where(model.id == existing_record.id).values(**data))
            print("Updated")
    else:
        session.execute(insert(model).values(**data))
        print("Inserted")
