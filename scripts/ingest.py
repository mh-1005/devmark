"""Pull activity from every connector into PostgreSQL.

Run:  uv run python -m scripts.ingest
"""

from app.connectors import ALL_CONNECTORS
from app.database.database import init_db
from app.services.ingestion import describe, ingest

init_db()
for result in ingest([cls() for cls in ALL_CONNECTORS]):
    print(describe(result))
