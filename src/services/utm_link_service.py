import logging
from typing import List, Sequence

from config import Config

from src.database.db import get_session
from src.database.models import UTMLink
from src.factories.utm_link_factory import UTMLinkFactory
from src.repositories.utm_link_repository import check_if_exist, save_link
from src.utils.exceptions.short_link_exception import ShortLinkCreationError
from src.utils.extarnal_api.short_io import ShortLinkManager


def create_link(
    url: str,
    campaign_source: str,
    campaign_content: str,
    domain: str,
    campaign_medium: str,
    campaign_name: str,
    slug: str,
) -> dict[str, str]:
    try:
        with get_session() as session:
            if check_if_exist(session, url, campaign_source, campaign_content, campaign_medium, campaign_name):
                return {"error_message": "Link already exists in database"}

            short_link_manager = ShortLinkManager(api_key=Config.SHORT_IO_API_KEY)

            link = UTMLinkFactory(short_link_manager).create_utm_link(
                url, campaign_source, campaign_content, domain, campaign_medium, campaign_name, slug
            )

            save_link(session, link)
            return {"short_url": link.short_secure_url}

    except ShortLinkCreationError as e:
        logging.error(f"Error creating short link: {e}")
        return {"error_message": f"Error creating short link: {e}"}

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {"error_message": "Unexpected error"}


def get_filtered_links(
    self,
    urls: List[str] | None = None,
    campaign_sources: List[str] | None = None,
    campaign_mediums: List[str] | None = None,
    campaign_names: List[str] | None = None,
    campaign_contents: List[str] | None = None,
) -> Sequence[UTMLink]:
    with get_session() as session:
        return self.utm_link_repository.get_filtered_links(
            session, urls, campaign_sources, campaign_mediums, campaign_names, campaign_contents
        )
