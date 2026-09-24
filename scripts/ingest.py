"""Pull activity from every connector into PostgreSQL.

Run:  uv run python -m scripts.ingest
"""

from app.connectors.github import GitHubConnector
from app.database.database import init_db
from app.services.ingestion import ingest

init_db()
ingest([GitHubConnector()])
