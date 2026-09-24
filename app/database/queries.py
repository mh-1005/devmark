"""Read queries used by the dashboard. Keep them small and readable."""

from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Activity


def get_recent_activities(limit: int = 50) -> list[Activity]:
    with SessionLocal() as session:
        stmt = select(Activity).order_by(Activity.timestamp.desc()).limit(limit)
        return list(session.scalars(stmt))
