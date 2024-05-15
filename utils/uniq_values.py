from sqlalchemy import distinct
from app import db
from models import UTMLink, ExcludedOption


def unique_list_tags():

    unique_url = db.session.query(distinct(UTMLink.url)). \
        filter(~UTMLink.url.in_(db.session.query(ExcludedOption.option_value). \
                                filter(ExcludedOption.option_type == 'urls[]'))).all()

    unique_campaign_content = db.session.query(distinct(UTMLink.campaign_content)). \
        filter(~UTMLink.campaign_content.in_(db.session.query(ExcludedOption.option_value). \
                                             filter(ExcludedOption.option_type == 'campaign_contents[]'))).all()

    unique_campaign_source = db.session.query(distinct(UTMLink.campaign_source)). \
        filter(~UTMLink.campaign_source.in_(db.session.query(ExcludedOption.option_value). \
                                            filter(ExcludedOption.option_type == 'campaign_sources[]'))).all()

    unique_campaign_medium = db.session.query(distinct(UTMLink.campaign_medium)). \
        filter(~UTMLink.campaign_medium.in_(db.session.query(ExcludedOption.option_value). \
                                            filter(ExcludedOption.option_type == 'campaign_mediums[]'))).all()

    unique_campaign_name = db.session.query(distinct(UTMLink.campaign_name)). \
        filter(~UTMLink.campaign_name.in_(db.session.query(ExcludedOption.option_value). \
                                          filter(ExcludedOption.option_type == 'campaign_names[]'))).all()

    # Преобразование результатов в списки уникальных значений
    unique_url = [item[0] for item in unique_url]
    unique_campaign_content = [item[0] for item in unique_campaign_content]
    unique_campaign_source = [item[0] for item in unique_campaign_source]
    unique_campaign_medium = [item[0] for item in unique_campaign_medium]
    unique_campaign_name = [item[0] for item in unique_campaign_name]

    return unique_url, unique_campaign_content, unique_campaign_source, unique_campaign_medium, unique_campaign_name
