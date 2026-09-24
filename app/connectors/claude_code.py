"""Claude Code → ASSIST. One activity per session, parsed from the local session logs.

Claude Code writes one JSONL file per session under ~/.claude/projects/<project>/<session-id>.jsonl.
We read only timestamps, record types and the working directory. Never the conversation text.
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

IDLE_GAP_SECONDS = 30 * 60  # a pause longer than this is "away", not part of the session

from app.connectors.base import BaseConnector
from app.database.models import Activity, Category


class ClaudeCodeConnector(BaseConnector):
    source = "claude_code"
    category = Category.ASSIST.value
    local = True

    def __init__(self) -> None:
        self.projects_dir = Path(os.getenv("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()

    def is_configured(self) -> bool:
        return self.projects_dir.is_dir()

    def fetch(self) -> list[dict]:
        sessions = []
        for path in self.projects_dir.glob("*/*.jsonl"):
            summary = self._summarize(path)
            if summary:
                sessions.append(summary)
        return sessions

    @staticmethod
    def _summarize(path: Path) -> dict | None:
        first = None
        prev = None
        active_seconds = 0.0
        cwd = None
        user_msgs = assistant_msgs = 0
        with path.open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("isSidechain"):  # subagent traffic, not the user's own turns
                    continue
                kind = r.get("type")
                if kind == "user" and not r.get("toolUseResult"):
                    user_msgs += 1
                elif kind == "assistant":
                    assistant_msgs += 1
                else:
                    continue
                ts = r.get("timestamp")
                if ts:
                    t = datetime.fromisoformat(ts)
                    first = first or t
                    # Active time = sum of gaps between messages, skipping long idle pauses.
                    # A session resumed days later would otherwise count the whole gap.
                    if prev is not None:
                        gap = (t - prev).total_seconds()
                        if 0 <= gap <= IDLE_GAP_SECONDS:
                            active_seconds += gap
                    prev = t
                cwd = cwd or r.get("cwd")
        if first is None or user_msgs == 0:
            return None
        return {
            "session_id": path.stem,
            "project": Path(cwd).name if cwd else path.parent.name,
            "started": first,
            "active_seconds": int(active_seconds),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
        }

    def normalize(self, raw: list[dict]) -> list[Activity]:
        out = []
        for s in raw:
            out.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="session",
                    title=f"Session — {s['project']}",
                    timestamp=s["started"],
                    duration_seconds=s["active_seconds"],
                    external_id=s["session_id"],
                    meta={
                        "project": s["project"],
                        "user_messages": s["user_messages"],
                        "assistant_messages": s["assistant_messages"],
                    },
                )
            )
        return out

    def mock(self) -> list[Activity]:
        rng = random.Random(3)
        projects = ["digital-log", "study-arc", "dotfiles", "medallion-data-warehouse"]
        now = datetime.now(timezone.utc)
        out = []
        for i in range(14):
            project = rng.choice(projects)
            minutes = rng.choice([12, 25, 40, 55, 70, 95, 130])
            out.append(
                Activity(
                    source=self.source,
                    category=self.category,
                    activity_type="session",
                    title=f"Session — {project}",
                    timestamp=now - timedelta(days=rng.randint(0, 20), hours=rng.randint(9, 23), minutes=rng.randint(0, 59)),
                    duration_seconds=minutes * 60,
                    external_id=f"mock-cc-{i}",
                    meta={"project": project, "user_messages": minutes // 3, "assistant_messages": minutes // 2},
                )
            )
        return out
