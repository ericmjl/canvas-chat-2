"""Database setup for Canvas Chat API."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from canvas_chat_2.api.settings import get_settings


class Base(DeclarativeBase):
    """Base SQLAlchemy declarative class."""


settings = get_settings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session.

    :yields Session: SQLAlchemy session.
    """

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables and ensure a default provider row exists."""

    from canvas_chat_2.api.models import ProviderConfig

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        existing_default = session.scalar(
            select(ProviderConfig).where(
                ProviderConfig.id == settings.default_provider_id
            )
        )
        if existing_default is None:
            default_provider = ProviderConfig(
                id=settings.default_provider_id,
                litellm_model=settings.default_litellm_model,
                is_active=True,
            )
            session.add(default_provider)
            session.commit()
