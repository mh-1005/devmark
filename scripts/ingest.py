"""Pull activity from every connector into PostgreSQL.

Run:  uv run python -m scripts.ingest
"""

from app.connectors.claude_code import ClaudeCodeConnector
from app.connectors.github import GitHubConnector
from app.connectors.leetcode import LeetCodeConnector
from app.connectors.todoist import TodoistConnector
from app.database.database import init_db
from app.services.ingestion import ingest

CONNECTORS = [GitHubConnector(), LeetCodeConnector(), TodoistConnector(), ClaudeCodeConnector()]

init_db()
ingest(CONNECTORS)
