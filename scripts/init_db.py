"""Create the tables. Safe to run more than once.

Run:  uv run python -m scripts.init_db
"""

from app.database.database import init_db

init_db()
print("Tables ready.")
