import datetime
from typing import List

from pydantic import BaseModel


class ManageExclusionsForm(BaseModel):
    url: List[str] | None = None
    campaign_source: List[str] | None = None
    campaign_medium: List[str] | None = None
    campaign_content: List[str] | None = None
    campaign_name: List[str] | None = None
    date_from: datetime.date
    date_to: datetime.date
