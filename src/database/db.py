from contextlib import contextmanager
from typing import Any, Generator, Type, Annotated

from config import Config
from sqlalchemy import create_engine, String
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, mapped_column

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define custom types for columns
str255 = Annotated[str, 255]
str50 = Annotated[str, 50]
str20 = Annotated[str, 20]
intpk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    type_annotation_map = {
        str50: String(50),
        str255: String(255),
        str20: String(20)
    }


@contextmanager
def get_session() -> Generator[Session, Any, Any]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")
        raise
    except OperationalError as e:
        session.rollback()
        print(f"OperationalError: {e}")
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"SQLAlchemyError: {e}")
        raise
    except Exception as e:
        session.rollback()
        print(f"Unhandled Exception: {e}")
        raise
    finally:
        session.close()
