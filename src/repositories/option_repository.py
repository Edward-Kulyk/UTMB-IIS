from typing import Any

from sqlalchemy import delete, distinct, select
from sqlalchemy.orm import Session

from src.database.models import ExcludedOption, UTMLink


def unique_list(session: Session, field: str) -> list[Any] | Any:
    field_attr = getattr(UTMLink, field)
    return (
        session.execute(
            select(distinct(field_attr)).where(
                ~field_attr.in_(select(ExcludedOption.option_value).where(ExcludedOption.option_type == field))
            )
        )
        .scalars()
        .all()
    )


def excluded_list(session: Session, option_type: str) -> list[Any] | Any:
    return (
        session.execute(select(ExcludedOption.option_value).where(ExcludedOption.option_type == option_type))
        .scalars()
        .all()
    )


def add_excluded_option(session: Session, option_type: str, option_value: str) -> None:
    option = ExcludedOption(option_type=option_type, option_value=option_value)
    session.add(option)


def delete_excluded_option(session: Session, option_type: str, option_value: str) -> None:
    session.execute(
        delete(ExcludedOption).where(
            ExcludedOption.option_type == option_type, ExcludedOption.option_value == option_value
        )
    )
