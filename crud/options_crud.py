from typing import Any

import sqlalchemy
from sqlalchemy import delete, distinct, select
from sqlalchemy.orm import Session

from models import ExcludedOption, UTMLink


def unique_list(db: Session, field: str) -> list[Any] | Any:
    # Received model attribute
    field_attr = getattr(UTMLink, field)

    stmt: sqlalchemy.Select = select(distinct(field_attr)).where(
        ~field_attr.in_(select(ExcludedOption.option_value).where(ExcludedOption.option_type == field))
    )

    unique_values = db.execute(stmt).scalars().all()
    return unique_values


def excluded_list(db: Session, option_type: str) -> list[Any] | Any:
    stmt = select(ExcludedOption.option_value).where(ExcludedOption.option_type == option_type)
    option_list = db.execute(stmt).scalars().all()
    return option_list


def add_excluded_option(db: Session, option_type: str, option_value: str) -> None:
    option = ExcludedOption(option_type=option_type, option_value=option_value)
    db.add(option)
    db.commit()


def delete_excluded_option(db: Session, option_type: str, option_value: str) -> None:
    stmt = delete(ExcludedOption).where(
        ExcludedOption.option_type == option_type, ExcludedOption.option_value == option_value
    )
    db.execute(stmt)
    db.commit()
