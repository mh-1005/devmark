"""Dashboard queries, written as SQL on purpose so the analytics stay readable.

Every function takes the same two filters:
  days    None = all time, 1 = today, 7 = last 7 days (local midnight boundaries)
  source  None = all sources, or one of "github" / "leetcode" / "todoist" / "claude_code"
"""

import os

from sqlalchemy import text

from app.database.database import engine

TZ = os.getenv("TIMEZONE", "UTC")


def _where(days: int | None, source: str | None, *extra: str) -> tuple[str, dict]:
    """Build the WHERE clause once so every query filters the same way."""
    clauses = list(extra)
    params: dict = {"tz": TZ}
    if days is not None:
        # Local midnight (days-1) days ago, converted back to an absolute instant.
        clauses.append(
            "timestamp >= (date_trunc('day', now() AT TIME ZONE :tz) - make_interval(days => :back)) AT TIME ZONE :tz"
        )
        params["back"] = days - 1
    if source:
        clauses.append("source = :source")
        params["source"] = source
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params


def _run(sql: str, params: dict) -> list[dict]:
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(text(sql), params).mappings()]


# ---- tiles -----------------------------------------------------------------

def build_summary(days, source) -> dict:
    where, p = _where(days, source, "category = 'BUILD'")
    return _run(f"""
        SELECT count(*) FILTER (WHERE activity_type = 'commit')        AS commits,
               count(*) FILTER (WHERE activity_type = 'pull_request')  AS prs,
               count(DISTINCT metadata->>'repo')                       AS repos
        FROM activities {where}
    """, p)[0]


def learn_summary(days, source) -> dict:
    where, p = _where(days, source, "category = 'LEARN'")
    return _run(f"""
        SELECT count(*)                                                   AS problems,
               count(*) FILTER (WHERE metadata->>'difficulty' = 'Easy')   AS easy,
               count(*) FILTER (WHERE metadata->>'difficulty' = 'Medium') AS medium,
               count(*) FILTER (WHERE metadata->>'difficulty' = 'Hard')   AS hard
        FROM activities {where}
    """, p)[0]


def do_summary(days, source) -> dict:
    where, p = _where(days, source, "category = 'DO'")
    return _run(f"""
        SELECT count(*)                            AS tasks,
               count(DISTINCT metadata->>'project') AS projects
        FROM activities {where}
    """, p)[0]


def assist_summary(days, source) -> dict:
    where, p = _where(days, source, "category = 'ASSIST'")
    return _run(f"""
        SELECT count(*)                                            AS sessions,
               coalesce(sum(duration_seconds), 0) / 3600.0         AS hours,
               count(DISTINCT metadata->>'project')                AS projects,
               coalesce(sum((metadata->>'user_messages')::int), 0) AS prompts
        FROM activities {where}
    """, p)[0]


# ---- timeline --------------------------------------------------------------

def timeline(days, source, limit: int = 200) -> list[dict]:
    where, p = _where(days, source)
    return _run(f"""
        SELECT timestamp AT TIME ZONE :tz AS local_ts,
               source, category, activity_type, title, duration_seconds, metadata
        FROM activities {where}
        ORDER BY timestamp DESC
        LIMIT :limit
    """, {**p, "limit": limit})


# ---- charts ----------------------------------------------------------------

def per_day(days, source) -> list[dict]:
    """Activity count per local day and category. Days with no activity are simply absent."""
    where, p = _where(days, source)
    return _run(f"""
        SELECT (timestamp AT TIME ZONE :tz)::date AS day, category, count(*) AS n
        FROM activities {where}
        GROUP BY 1, 2
        ORDER BY 1
    """, p)


def by_weekday(days, source) -> list[dict]:
    """Activity count by ISO weekday (1 = Monday ... 7 = Sunday)."""
    where, p = _where(days, source)
    return _run(f"""
        SELECT extract(isodow FROM timestamp AT TIME ZONE :tz)::int AS dow, count(*) AS n
        FROM activities {where}
        GROUP BY 1
        ORDER BY 1
    """, p)


def by_source(days, source) -> list[dict]:
    where, p = _where(days, source)
    return _run(f"""
        SELECT source, category, count(*) AS n
        FROM activities {where}
        GROUP BY 1, 2
        ORDER BY n DESC
    """, p)


def source_comparison(days: int, source) -> list[dict]:
    """Per source: activity count in the current window vs the same-length window right before it."""
    src_clause = "AND source = :source" if source else ""
    return _run(f"""
        WITH bounds AS (
            SELECT (date_trunc('day', now() AT TIME ZONE :tz) - make_interval(days => :back)) AT TIME ZONE :tz AS start
        )
        SELECT source, category,
               count(*) FILTER (WHERE timestamp >= start)  AS current,
               count(*) FILTER (WHERE timestamp <  start)  AS previous
        FROM activities, bounds
        WHERE timestamp >= start - make_interval(days => :days) {src_clause}
        GROUP BY 1, 2
        ORDER BY current DESC
    """, {"tz": TZ, "back": days - 1, "days": days, **({"source": source} if source else {})})
