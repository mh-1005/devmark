"""Run connectors and save their activities. Re-running is safe: duplicates are skipped."""

from sqlalchemy.dialects.postgresql import insert

from app.connectors.base import BaseConnector
from app.database.database import SessionLocal
from app.database.models import Activity


def save_activities(activities: list[Activity]) -> int:
    """Insert rows, skipping any (source, external_id) that already exists. Returns rows inserted."""
    if not activities:
        return 0
    stmt = (
        insert(Activity)
        .values([a.as_row() for a in activities])
        .on_conflict_do_nothing(constraint="uq_source_external_id")
        .returning(Activity.id)  # RETURNING gives us the ids actually inserted; rowcount is unreliable here
    )
    with SessionLocal() as session:
        inserted_ids = session.execute(stmt).all()
        session.commit()
        return len(inserted_ids)


def ingest(connectors: list[BaseConnector]) -> None:
    for connector in connectors:
        activities, mode = connector.run()
        inserted = save_activities(activities)
        print(f"{connector.source:<10} [{mode}]  fetched {len(activities):>3}  inserted {inserted:>3}  skipped {len(activities) - inserted:>3}")
