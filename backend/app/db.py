"""Database engine and session factory (SQLAlchemy 2.x, synchronous)."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base


def make_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        # SQLite is for local development and tests. Requests run in worker threads, so allow that.
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool  # an in-memory database exists per connection, so share one
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True)  # pre-ping replaces connections the server has dropped


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def create_tables(engine: Engine) -> None:
    """Creates any missing tables. Fine for getting started; use Alembic migrations before changing the schema in production."""
    Base.metadata.create_all(engine)
