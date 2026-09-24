"""Fill the dashboard with realistic fake activity, or remove it again.

Run:  uv run python -m scripts.seed_mock          # add mock rows for every source
      uv run python -m scripts.seed_mock --clear  # remove them (real rows are untouched)

Mock rows are recognisable by their external_id, which always starts with "mock-".
"""

import sys

from sqlalchemy import delete

from app.connectors import ALL_CONNECTORS
from app.database.database import SessionLocal, init_db
from app.database.models import Activity
from app.services.ingestion import save_activities

init_db()

if "--clear" in sys.argv:
    with SessionLocal() as session:
        removed = session.execute(delete(Activity).where(Activity.external_id.like("mock-%"))).rowcount
        session.commit()
    print(f"Removed {removed} mock activities.")
else:
    for cls in ALL_CONNECTORS:
        connector = cls()
        activities = connector.mock()
        inserted = save_activities(activities)
        print(f"{connector.source:<12} seeded {inserted:>3} of {len(activities):>3} mock activities")
    print("Open the dashboard; the header shows 'INCLUDES MOCK DATA' until you run --clear.")
