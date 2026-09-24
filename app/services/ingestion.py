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


def ingest(connectors: list[BaseConnector]) -> list[dict]:
    """Run each connector and save what it returns. One failing source never blocks the others."""
    results = []
    for connector in connectors:
        try:
            activities, mode = connector.run()
            inserted = save_activities(activities)
            results.append({"source": connector.source, "mode": mode, "fetched": len(activities), "inserted": inserted})
        except Exception as exc:  # noqa: BLE001  (a bad token or a network blip should not abort the sync)
            results.append({"source": connector.source, "mode": "error", "fetched": 0, "inserted": 0, "error": str(exc)[:200]})
    return results


def describe(result: dict) -> str:
    r = result
    if r["mode"] == "error":
        return f"{r['source']:<12} [error]    {r['error']}"
    return f"{r['source']:<12} [{r['mode']}]  fetched {r['fetched']:>3}  inserted {r['inserted']:>3}  skipped {r['fetched'] - r['inserted']:>3}"
