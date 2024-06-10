from typing import Optional

from pydantic import BaseModel


class LinkCreationForm(BaseModel):
    url: str
    campaign_source: str
    campaign_content: Optional[str]
    domain: str
    campaign_medium: str
    campaign_name: str
    slug: str | None = ""
