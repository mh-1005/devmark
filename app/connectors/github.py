"""GitHub → BUILD. Commits and pull requests authored by the user."""

import os
import random
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import BaseConnector
from app.database.models import Activity, Category

API = "https://api.github.com"
DAYS_BACK = 90


class GitHubConnector(BaseConnector):
    source = "github"
    category = Category.BUILD.value

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.username = os.getenv("GITHUB_USERNAME", "")

    def is_configured(self) -> bool:
        return bool(self.token and self.username)

    def status(self) -> str:
        return f"connected · {self.username}" if self.is_configured() else "not connected"

    # ---- fetch -----------------------------------------------------------

    def fetch(self) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).date().isoformat()
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}

        with httpx.Client(base_url=API, headers=headers, timeout=20) as client:
            commits = self._search(client, "/search/commits", f"author:{self.username} author-date:>={since}")
            prs = self._search(client, "/search/issues", f"author:{self.username} type:pr created:>={since}")

        # Tag each record so normalize() knows which shape it is looking at.
        return [{"kind": "commit", **c} for c in commits] + [{"kind": "pr", **p} for p in prs]

    @staticmethod
    def _search(client: httpx.Client, path: str, query: str) -> list[dict]:
        """GitHub search endpoints page at 100 items. Keep asking until a page comes back short."""
        items: list[dict] = []
        page = 1
        while True:
            resp = client.get(path, params={"q": query, "per_page": 100, "page": page})
            resp.raise_for_status()
            batch = resp.json()["items"]
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1

    # ---- normalize -------------------------------------------------------

    def normalize(self, raw: list[dict]) -> list[Activity]:
        return [self._commit(r) if r["kind"] == "commit" else self._pr(r) for r in raw]

    def _commit(self, c: dict) -> Activity:
        return Activity(
            source=self.source,
            category=self.category,
            activity_type="commit",
            title=c["commit"]["message"].splitlines()[0][:255],
            timestamp=datetime.fromisoformat(c["commit"]["author"]["date"]),
            external_id=c["sha"],
            meta={"repo": c["repository"]["full_name"], "url": c["html_url"]},
        )

    def _pr(self, p: dict) -> Activity:
        repo = p["repository_url"].removeprefix(f"{API}/repos/")
        return Activity(
            source=self.source,
            category=self.category,
            activity_type="pull_request",
            title=p["title"][:255],
            timestamp=datetime.fromisoformat(p["created_at"]),
            external_id=f"pr-{p['id']}",
            meta={"repo": repo, "state": p["state"], "url": p["html_url"]},
        )

    # ---- mock ------------------------------------------------------------

    def mock(self) -> list[Activity]:
        rng = random.Random(42)  # seeded → same fake data every run
        repos = ["acme/inventory-api", "acme/web-client", "acme/infra"]
        messages = [
            "add pagination to orders endpoint", "fix null price on imported SKUs", "cache product lookups",
            "migrate to typed config", "add retry to webhook sender", "upgrade CI runner image",
            "handle empty cart on checkout", "add stock alerts", "tighten CORS rules", "remove dead feature flag",
        ]
        now = datetime.now(timezone.utc)
        activities = []
        for i in range(70):
            ts = now - timedelta(days=rng.randint(0, 80), hours=rng.randint(8, 23), minutes=rng.randint(0, 59))
            activities.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="commit",
                    title=rng.choice(messages),
                    timestamp=ts,
                    external_id=f"mock-commit-{i}",
                    meta={"repo": rng.choice(repos)},
                )
            )
        for i in range(6):
            activities.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="pull_request",
                    title=f"PR #{i + 1}: {rng.choice(messages)}",
                    timestamp=now - timedelta(days=rng.randint(1, 75), hours=rng.randint(9, 20)),
                    external_id=f"mock-pr-{i}",
                    meta={"repo": rng.choice(repos), "state": "open" if i == 0 else "closed"},
                )
            )
        return activities
