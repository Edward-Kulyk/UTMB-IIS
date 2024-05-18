from app import db
from sqlalchemy.orm import relationship


class ExcludedOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_type = db.Column(db.String(50), nullable=False)
    option_value = db.Column(db.String(255), nullable=False)


class UTMLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    campaign_content = db.Column(db.String(50), nullable=True)
    campaign_source = db.Column(db.String(50), nullable=False)
    campaign_medium = db.Column(db.String(50), nullable=False)
    campaign_name = db.Column(db.String(50), db.ForeignKey("campaign.name"), nullable=False)
    domain = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    short_id = db.Column(db.String(20), nullable=True)
    short_secure_url = db.Column(db.String(20), nullable=True)

    campaign = relationship("Campaign", back_populates="links")

    clicks = relationship("ClicksDate", back_populates="link")


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    url_by_default = db.Column(db.String(255), nullable=True)
    domain_by_default = db.Column(db.String(20), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    hide = db.Column(db.Boolean, default=False)

    links = relationship("UTMLink", back_populates="campaign")


class ClicksDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey("utm_link.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    clicks_count = db.Column(db.Integer, default=0)

    link = relationship("UTMLink", back_populates="clicks")


class GoogleAnalyticsDataGraph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    session_source_medium = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    active_users = db.Column(db.Integer, nullable=False)
    sessions = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(255), nullable=False)


class GoogleAnalyticsDataTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_source_medium = db.Column(db.String(255))
    url = db.Column(db.String(255))
    active_users = db.Column(db.Integer)
    sessions = db.Column(db.Integer)
    average_session_duration = db.Column(db.Integer)
    bounce_rate = db.Column(db.Float)
    content = db.Column(db.String(255))


class Blogger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    yt_channel_id = db.Column(db.String, unique=True)
    yt_avg = db.Column(db.Integer, default=0)
    ig_url = db.Column(db.String)
    ig_avg = db.Column(db.Integer, default=0)
