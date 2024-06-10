from src.database.models import UTMLink
from src.utils.exceptions.short_link_exception import ShortLinkCreationError
from src.utils.extarnal_api.short_io import ShortLinkManager


class UTMLinkFactory:
    def __init__(self, short_link_service: ShortLinkManager):
        self.short_link_service = short_link_service

    def create_utm_link(
        self,
        url: str,
        campaign_source: str,
        campaign_content: str,
        domain: str,
        campaign_medium: str,
        campaign_name: str,
        slug: str,
    ) -> UTMLink:
        short_link_data = self.short_link_service.create_short_link(domain, slug, url)

        if short_link_data.get("error"):
            raise ShortLinkCreationError(short_link_data["error"], 400)

        if slug == "":
            slug = short_link_data["path"]

        short_id = short_link_data["idString"]
        short_secure_url = short_link_data["secureShortURL"]

        return UTMLink(
            url=url,
            campaign_source=campaign_source,
            domain=domain,
            campaign_medium=campaign_medium,
            campaign_content=campaign_content,
            campaign_name=campaign_name,
            slug=slug,
            short_id=short_id,
            short_secure_url=short_secure_url,
        )
