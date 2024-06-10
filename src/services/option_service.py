from typing import Dict

from src.database.db import get_session
from src.repositories.option_repository import add_excluded_option, delete_excluded_option, excluded_list, unique_list


def get_options_context(action: str) -> Dict[str, list]:

    action_func = unique_list if action == "unique" else excluded_list
    with get_session() as session:
        return {
            "campaign_content": action_func(session, "campaign_content"),
            "campaign_source": action_func(session, "campaign_source"),
            "campaign_medium": action_func(session, "campaign_medium"),
            "campaign_name": action_func(session, "campaign_name"),
            "campaign_url": action_func(session, "url"),
        }


def process_option_form(form_data: Dict, action: str) -> None:

    action_func = add_excluded_option if action == "add" else delete_excluded_option
    with get_session() as session:
        for field_name, values in form_data.items():
            if values is not None:
                for value in values:
                    action_func(session, field_name, value)
