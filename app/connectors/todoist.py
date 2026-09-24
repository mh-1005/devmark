"""Todoist → DO. Task completions read from the Todoist activity log (API v1).

Why the activity log and not the "completed tasks" endpoint: completing a recurring task
("water plants, every day") does not mark it completed, it reschedules it. Only the activity
log records every tick, one-off and recurring alike.
"""

import os
import random
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import BaseConnector
from app.database.models import Activity, Category

API = "https://api.todoist.com/api/v1"
MAX_PAGES = 10  # 100 events per page; free accounts only keep about a week of log anyway


class TodoistConnector(BaseConnector):
    source = "todoist"
    category = Category.DO.value

    def __init__(self) -> None:
        self.token = os.getenv("TODOIST_API_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.token)

    def fetch(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self.token}"}
        with httpx.Client(base_url=API, headers=headers, timeout=20) as client:
            projects = {p["id"]: p["name"] for p in self._paged(client, "/projects", {})}
            events = self._paged(client, "/activities", {"object_type": "item", "event_type": "completed", "limit": 100})
        # Attach the project name now so normalize() needs no lookup table.
        return [{**e, "project_name": projects.get(e.get("parent_project_id"), "Inbox")} for e in events]

    @staticmethod
    def _paged(client: httpx.Client, path: str, params: dict) -> list[dict]:
        """Todoist v1 pages with a cursor: keep requesting until next_cursor is null."""
        items: list[dict] = []
        cursor = None
        for _ in range(MAX_PAGES):
            resp = client.get(path, params={**params, **({"cursor": cursor} if cursor else {})})
            resp.raise_for_status()
            body = resp.json()
            items.extend(body.get("results") or body.get("items") or [])
            cursor = body.get("next_cursor")
            if not cursor:
                break
        return items

    def normalize(self, raw: list[dict]) -> list[Activity]:
        out: list[Activity] = []
        seen: set[tuple[str, object]] = set()
        for e in raw:
            ts = datetime.fromisoformat(e["event_date"])
            # A task counts once per day: ticking, un-ticking and re-ticking is one completion.
            key = (e["object_id"], ts.date())
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="task_completed",
                    title=((e.get("extra_data") or {}).get("content") or "Task")[:255],
                    timestamp=ts,
                    external_id=e["id"],  # the log event id: unique per completion, stable across runs
                    meta={"project": e["project_name"], "task_id": e["object_id"]},
                )
            )
        return out

    def mock(self) -> list[Activity]:
        rng = random.Random(11)
        tasks = {
            "Uni": ["Submit DSA assignment", "Review SQL joins notes", "Read OS chapter 4", "Prepare lab report",
                    "Practice recursion problems", "Watch DBMS lecture", "Revise for quiz"],
            "Projects": ["Write README", "Fix timezone bug", "Add charts to dashboard", "Refactor connector",
                         "Plan next milestone", "Set up PostgreSQL"],
            "Life": ["Groceries", "Call home", "Gym", "Laundry", "Pay phone bill"],
        }
        now = datetime.now(timezone.utc)
        out = []
        for i in range(36):
            project = rng.choice(list(tasks))
            out.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="task_completed",
                    title=rng.choice(tasks[project]),
                    timestamp=now - timedelta(days=rng.randint(0, 20), hours=rng.randint(7, 23), minutes=rng.randint(0, 59)),
                    external_id=f"mock-td-{i}",
                    meta={"project": project, "task_id": f"mock-task-{i}"},
                )
            )
        return out
