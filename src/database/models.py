from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.db import Base, str255, str50, intpk, str20


class ExcludedOption(Base):
    __tablename__ = "excluded_options"
    id: Mapped[intpk]
    option_type: Mapped[str50]
    option_value: Mapped[str255]


class UTMLink(Base):
    __tablename__ = "utm_link"
    id: Mapped[intpk]
    url: Mapped[str255]
    campaign_content: Mapped[Optional[str50]]
    campaign_source: Mapped[str50]
    campaign_medium: Mapped[str50]
    campaign_name: Mapped[str50] = mapped_column(String(50), ForeignKey("campaign.name"), nullable=False)
    domain: Mapped[str20]
    slug: Mapped[str50]
    short_id: Mapped[Optional[str20]]
    short_secure_url: Mapped[Optional[str20]]

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="links")
    clicks: Mapped[List["ClicksDate"]] = relationship("ClicksDate", back_populates="link")


class Campaign(Base):
    __tablename__ = "campaign"
    id: Mapped[intpk]
    name: Mapped[str50]
    url_by_default: Mapped[Optional[str255]]
    domain_by_default: Mapped[Optional[str20]]
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    hide: Mapped[bool] = mapped_column(Boolean, default=False)

    links: Mapped[List[UTMLink]] = relationship("UTMLink", back_populates="campaign")


class ClicksDate(Base):
    __tablename__ = "clicks_date"
    id: Mapped[intpk]
    link_id: Mapped[int] = mapped_column(Integer, ForeignKey("utm_link.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0)

    link: Mapped["UTMLink"] = relationship("UTMLink", back_populates="clicks")


class GoogleAnalyticsData(Base):
    __tablename__ = "google_analytics_data"
    id: Mapped[intpk]
    date: Mapped[date] = mapped_column(Date, nullable=False)
    session_source_medium: Mapped[str255]
    url: Mapped[str255]
    active_users: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(String)
    bounce_rate: Mapped[int] = mapped_column(Integer)
    average_session_duration: Mapped[int] = mapped_column(Integer)
