from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class ExcludedOption(Base):
    __tablename__ = "excluded_options"
    id = Column(Integer, primary_key=True)
    option_type = Column(String(50), nullable=False)
    option_value = Column(String(255), nullable=False)


class UTMLink(Base):
    __tablename__ = "utm_link"
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    campaign_content = Column(String(50), nullable=True)
    campaign_source = Column(String(50), nullable=False)
    campaign_medium = Column(String(50), nullable=False)
    campaign_name = Column(String(50), ForeignKey("campaign.name"), nullable=False)
    domain = Column(String(20), nullable=False)
    slug = Column(String(50), nullable=False)
    short_id = Column(String(20), nullable=True)
    short_secure_url = Column(String(20), nullable=True)

    campaign = relationship("Campaign", back_populates="links")
    clicks = relationship("ClicksDate", back_populates="link")


class Campaign(Base):
    __tablename__ = "campaign"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    url_by_default = Column(String(255), nullable=True)
    domain_by_default = Column(String(20), nullable=True)
    start_date = Column(Date, nullable=False)
    hide = Column(Boolean, default=False)

    links = relationship("UTMLink", back_populates="campaign")


class ClicksDate(Base):
    __tablename__ = "clicks_date"
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("utm_link.id"), nullable=False)
    date = Column(Date, nullable=False)
    clicks_count = Column(Integer, default=0)

    link = relationship("UTMLink", back_populates="clicks")


class GoogleAnalyticsDataGraph(Base):
    __tablename__ = "google_analytics_data_graph"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    session_source_medium = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    active_users = Column(Integer, nullable=False)
    sessions = Column(Integer, nullable=False)


class GoogleAnalyticsDataTable(Base):
    __tablename__ = "google_analytics_data_table"
    id = Column(Integer, primary_key=True)
    session_source_medium = Column(String(255))
    url = Column(String(255))
    active_users = Column(Integer)
    sessions = Column(Integer)
    average_session_duration = Column(Integer)
    bounce_rate = Column(Float)
    content = Column(String(255))


class Blogger(Base):
    __tablename__ = "blogger"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    yt_channel_id = Column(String, unique=True)
    yt_avg = Column(Integer, default=0)
    ig_url = Column(String)
    ig_avg = Column(Integer, default=0)
