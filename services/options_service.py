from werkzeug.datastructures import MultiDict

from crud import add_excluded_option, delete_excluded_option, excluded_list, unique_list
from database import get_session


def get_options_context(action: str) -> dict[str, list]:
    """
    Process option form data.

    Args:
        form_data (dict): Form data.
        action (str): Action to perform. Should be either 'unique' or 'excluded'.
    """
    action_func = unique_list if action == "unique" else excluded_list
    with get_session() as session:
        return {
            "campaign_content": action_func(session, "campaign_content"),
            "campaign_source": action_func(session, "campaign_source"),
            "campaign_medium": action_func(session, "campaign_medium"),
            "campaign_name": action_func(session, "campaign_name"),
            "campaign_url": action_func(session, "url"),
        }


def process_option_form(form_data: MultiDict, action: str) -> None:
    """
    Process option form data.

    Args:
        form_data (dict): Form data.
        action (str): Action to perform. Should be either 'add' or 'delete'.
    """

    action_func = add_excluded_option if action == "add" else delete_excluded_option
    with get_session() as session:
        for field_name, values in form_data.lists():
            for value in values:
                action_func(session, option_type=field_name, option_value=value)
