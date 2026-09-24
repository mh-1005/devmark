"""Create the tables and insert one test activity. Safe to run more than once.

Run:  uv run python -m scripts.init_db
"""

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.database.database import SessionLocal, init_db
from app.database.models import Activity, Category

init_db()

with SessionLocal() as session:
    count = session.scalar(select(func.count()).select_from(Activity))
    if count == 0:
        session.add(
            Activity(
                source="test",
                category=Category.BUILD.value,
                activity_type="commit",
                title="Hello from Step 2",
                timestamp=datetime.now(timezone.utc),
                meta={"note": "first row ever"},
                external_id="test-1",
            )
        )
        session.commit()
        print("Inserted 1 test activity.")
        count = 1
    print(f"activities table has {count} row(s).")
