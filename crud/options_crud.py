from typing import Any

import sqlalchemy
from sqlalchemy import delete, distinct, select
from sqlalchemy.orm import Session

from models import ExcludedOption, UTMLink


def unique_list(session: Session, field: str) -> list[Any] | Any:
    # Received model attribute
    field_attr = getattr(UTMLink, field)

    stmt: sqlalchemy.Select = select(distinct(field_attr)).where(
        ~field_attr.in_(select(ExcludedOption.option_value).where(ExcludedOption.option_type == field))
    )

    unique_values = session.execute(stmt).scalars().all()
    return unique_values


def excluded_list(session: Session, option_type: str) -> list[Any] | Any:
    stmt = select(ExcludedOption.option_value).where(ExcludedOption.option_type == option_type)
    return session.execute(stmt).scalars().all()


def add_excluded_option(session: Session, option_type: str, option_value: str) -> None:
    option = ExcludedOption(option_type=option_type, option_value=option_value)
    session.add(option)
    session.commit()


def delete_excluded_option(session: Session, option_type: str, option_value: str) -> None:
    stmt = delete(ExcludedOption).where(
        ExcludedOption.option_type == option_type, ExcludedOption.option_value == option_value
    )
    session.execute(stmt)
    session.commit()
