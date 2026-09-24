"""The unified Activity model. Every source normalizes into this one shape."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Category(str, enum.Enum):
    BUILD = "BUILD"    # GitHub
    LEARN = "LEARN"    # LeetCode
    TIME = "TIME"      # Google Calendar
    LISTEN = "LISTEN"  # Spotify
    READ = "READ"      # Goodreads
    DO = "DO"          # Todoist


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable for V1 (single local user). Becomes a foreign key when users arrive.
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source: Mapped[str] = mapped_column(String(32), index=True)          # "github", "spotify", ...
    category: Mapped[str] = mapped_column(String(16), index=True)        # one of Category
    activity_type: Mapped[str] = mapped_column(String(32))               # "commit", "listen", ...
    title: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Source-specific details (repo, artist, difficulty...). JSONB keeps us to one table.
    # Python attribute is `meta` because `metadata` is reserved by SQLAlchemy's Base.
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # The id the source uses (commit sha, track play id...). Lets re-ingestion skip duplicates.
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_source_external_id"),)

    def __repr__(self) -> str:
        return f"<Activity {self.source}/{self.activity_type} '{self.title}' @ {self.timestamp:%Y-%m-%d %H:%M}>"
