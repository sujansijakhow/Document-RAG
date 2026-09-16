"""SQLAlchemy engine/session wiring for the metadata store.

SQLite is used by default (zero external dependency, fine for a
take-home / small deployment) but `DATABASE_URL` can point at any
SQLAlchemy-supported SQL database (Postgres, MySQL, ...) without code
changes.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()
settings.ensure_data_dirs()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import booking, document  # noqa: F401

    Base.metadata.create_all(bind=engine)
