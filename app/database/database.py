"""Database connection. One engine, one session factory, one Base for all models."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import app.config  # noqa: F401  (importing it loads .env)

DATABASE_URL = os.environ["DATABASE_URL"]

# The engine owns a pool of connections to PostgreSQL. Create it once, reuse everywhere.
engine = create_engine(DATABASE_URL)

# A Session is a short-lived unit of work: open it, read/write, commit, close.
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Every model inherits from this so SQLAlchemy knows about all tables."""


def init_db() -> None:
    """Create any tables that don't exist yet. Safe to call repeatedly."""
    from app.database import models  # noqa: F401  (import registers the models on Base)

    Base.metadata.create_all(engine)
