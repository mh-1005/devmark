"""Todoist → DO. Completed tasks via the Todoist API v1."""

import os
import random
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import BaseConnector
from app.database.models import Activity, Category

API = "https://api.todoist.com/api/v1"
DAYS_BACK = 84  # the completed-tasks endpoint allows at most a 3-month window


class TodoistConnector(BaseConnector):
    source = "todoist"
    category = Category.DO.value

    def __init__(self) -> None:
        self.token = os.getenv("TODOIST_API_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.token)

    def fetch(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        params = {
            "since": (now - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "until": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 200,
        }
        with httpx.Client(base_url=API, headers={"Authorization": f"Bearer {self.token}"}, timeout=20) as client:
            projects = {p["id"]: p["name"] for p in self._paged(client, "/projects", {})}
            tasks = self._paged(client, "/tasks/completed/by_completion_date", params)
        # Attach the project name now so normalize() needs no lookup table.
        return [{**t, "project_name": projects.get(t.get("project_id"), "Inbox")} for t in tasks]

    @staticmethod
    def _paged(client: httpx.Client, path: str, params: dict) -> list[dict]:
        """Todoist v1 pages with a cursor: keep requesting until next_cursor is null."""
        items: list[dict] = []
        cursor = None
        while True:
            resp = client.get(path, params={**params, **({"cursor": cursor} if cursor else {})})
            resp.raise_for_status()
            body = resp.json()
            items.extend(body.get("items") or body.get("results") or [])
            cursor = body.get("next_cursor")
            if not cursor:
                return items

    def normalize(self, raw: list[dict]) -> list[Activity]:
        return [
            Activity(
                source=self.source,
                category=self.category,
                activity_type="task_completed",
                title=t["content"][:255],
                timestamp=datetime.fromisoformat(t["completed_at"]),
                # Recurring tasks reuse one id across completions, so include the time.
                external_id=f"{t['id']}-{t['completed_at']}",
                meta={"project": t["project_name"], "labels": t.get("labels", []), "due": (t.get("due") or {}).get("date")},
            )
            for t in raw
        ]

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
                    meta={"project": project, "labels": rng.choice([[], ["focus"], ["quick"]]), "due": None},
                )
            )
        return out
