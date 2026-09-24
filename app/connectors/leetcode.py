"""LeetCode → LEARN. Recent accepted submissions via the public GraphQL endpoint (no login)."""

import os
import random
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import BaseConnector
from app.database.models import Activity, Category

GRAPHQL = "https://leetcode.com/graphql"

RECENT_QUERY = """
query($u: String!) {
  recentAcSubmissionList(username: $u, limit: 20) { id title titleSlug timestamp lang }
}"""
DIFFICULTY_QUERY = "query($s: String!) { question(titleSlug: $s) { difficulty } }"


class LeetCodeConnector(BaseConnector):
    source = "leetcode"
    category = Category.LEARN.value

    def __init__(self) -> None:
        self.username = os.getenv("LEETCODE_USERNAME", "")

    def is_configured(self) -> bool:
        return bool(self.username)

    def fetch(self) -> list[dict]:
        headers = {"Content-Type": "application/json", "Referer": "https://leetcode.com"}
        with httpx.Client(headers=headers, timeout=20) as client:
            subs = self._gql(client, RECENT_QUERY, {"u": self.username})["recentAcSubmissionList"]
            # One small extra request per unique problem to get its difficulty (max 20).
            difficulty = {
                slug: self._gql(client, DIFFICULTY_QUERY, {"s": slug})["question"]["difficulty"]
                for slug in {s["titleSlug"] for s in subs}
            }
        return [{**s, "difficulty": difficulty[s["titleSlug"]]} for s in subs]

    @staticmethod
    def _gql(client: httpx.Client, query: str, variables: dict) -> dict:
        resp = client.post(GRAPHQL, json={"query": query, "variables": variables})
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"LeetCode GraphQL error: {body['errors']}")
        return body["data"]

    def normalize(self, raw: list[dict]) -> list[Activity]:
        return [
            Activity(
                source=self.source,
                category=self.category,
                activity_type="problem_solved",
                title=s["title"],
                timestamp=datetime.fromtimestamp(int(s["timestamp"]), tz=timezone.utc),
                external_id=s["id"],
                meta={"slug": s["titleSlug"], "difficulty": s["difficulty"], "lang": s["lang"]},
            )
            for s in raw
        ]

    def mock(self) -> list[Activity]:
        rng = random.Random(7)
        problems = [
            ("Two Sum", "Easy"), ("Valid Parentheses", "Easy"), ("Merge Two Sorted Lists", "Easy"),
            ("LRU Cache", "Medium"), ("Binary Tree Level Order Traversal", "Medium"),
            ("Longest Substring Without Repeating Characters", "Medium"), ("Coin Change", "Medium"),
            ("Course Schedule", "Medium"), ("Confirmation Rate", "Medium"), ("Trapping Rain Water", "Hard"),
            ("Median of Two Sorted Arrays", "Hard"), ("Odd Even Linked List", "Medium"),
        ]
        now = datetime.now(timezone.utc)
        return [
            Activity(
                source=self.source,
                category=self.category,
                activity_type="problem_solved",
                title=title,
                timestamp=now - timedelta(days=rng.randint(0, 20), hours=rng.randint(8, 23), minutes=rng.randint(0, 59)),
                external_id=f"mock-lc-{i}",
                meta={"slug": title.lower().replace(" ", "-"), "difficulty": diff, "lang": rng.choice(["python", "postgresql"])},
            )
            for i, (title, diff) in enumerate(problems)
        ]
