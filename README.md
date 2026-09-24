# DEVMARK

**Make your work visible.**

> Your GitHub commits, LeetCode solves, tasks, and AI coding sessions — brought together in one place.

Every commit, solved problem, completed task, or coding session is a **mark** of work.
DEVMARK collects them from the services you already use, normalizes them into one shape,
stores them in PostgreSQL, and shows them on one Streamlit page: four tiles, a 12-week
heatmap, a merged timeline of marks, and a few honest charts.

Built as a one-day MVP. Small on purpose.

## Architecture

```text
GitHub · LeetCode · Todoist · Claude Code
              ↓
      app/connectors/      one file per source: fetch() → normalize() → [Activity]
              ↓
      app/services/ingestion.py   INSERT ... ON CONFLICT DO NOTHING (safe to re-run)
              ↓
      PostgreSQL            one table: activities
              ↓
      app/database/queries.py     plain SQL for the analytics
              ↓
      app/dashboard.py      Streamlit + a little Plotly
```

Every source produces the same row:

| column | example |
|---|---|
| source | `github` |
| category | `BUILD` |
| activity_type | `commit` |
| title | `add GitHub connector` |
| timestamp | `2026-09-24 13:38+00` |
| duration_seconds | `4800` (Claude Code sessions only) |
| metadata (JSONB) | `{"repo": "mh-1005/devmark"}` |
| external_id | the source's own id, so re-ingesting never duplicates |

## Integrations

| Source | Category | What it records | How it connects |
|---|---|---|---|
| GitHub | Build | commits and pull requests you authored | fine-grained token, read-only |
| LeetCode | Learn | accepted submissions with difficulty and language | public username, no token |
| Todoist | Do | every task completion, recurring ones included | API token |
| Claude Code | Assist | one row per local session: active time, prompt count | reads `~/.claude/projects`, no token |

Adding a source is one file in `app/connectors/` plus one line in `app/connectors/__init__.py`.

## Tech stack

Python 3.12 · uv · PostgreSQL · SQLAlchemy 2 · Streamlit · Plotly · httpx · python-dotenv

No FastAPI, no Docker, no queue, no scheduler. If it grows, those can come later.

## Setup

You need PostgreSQL running locally and [uv](https://docs.astral.sh/uv/) installed.

```bash
git clone <this repo> && cd devmark
uv sync                                   # creates .venv and installs everything
createdb devmark                          # or: psql -c "CREATE DATABASE devmark"
cp .env.example .env                      # then set TIMEZONE, leave the rest for the sidebar
uv run python -m scripts.init_db          # creates the table
uv run streamlit run app/dashboard.py
```

**No accounts yet?** Seed fake data and look around:

```bash
uv run python -m scripts.seed_mock          # add
uv run python -m scripts.seed_mock --clear  # remove when you connect real accounts
```

**Connecting accounts.** Open the sidebar, paste your tokens under "Connect accounts", click
Save, then "Sync now". Tokens are written to `.env` on your machine and never shown again.
Where to get them:

- GitHub: Settings → Developer settings → Fine-grained tokens. Read-only `Contents` and `Pull requests`.
- LeetCode: just your username from `leetcode.com/u/<username>/`.
- Todoist: Settings → Integrations → Developer → API token.
- Claude Code: nothing to do. It finds `~/.claude/projects` on its own.

A source that isn't connected shows a "Not connected" tile and is left out of everything else.
Nothing is faked unless you ask for it.

**Syncing.** The page syncs on load if the last sync was more than 5 minutes ago, and
"Sync now" forces one. From the terminal: `uv run python -m scripts.ingest`. Open the
dashboard at least weekly: free Todoist accounts keep only about a week of activity log.

Editing `.env` by hand while the app is running is not picked up until you restart it;
the sidebar's Save button reloads it live.

## Environment variables

`.env.example` lists every variable. Copy it to `.env`, which is git-ignored.

| variable | purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://localhost:5432/devmark` |
| `TIMEZONE` | IANA name used for day boundaries and the timeline, e.g. `Asia/Karachi` |
| `USE_MOCK_DATA` | `true` makes every connector return fake data. Prefer the seeder. |
| `GITHUB_TOKEN`, `GITHUB_USERNAME` | GitHub |
| `LEETCODE_USERNAME` | LeetCode |
| `TODOIST_API_TOKEN` | Todoist |
| `CLAUDE_PROJECTS_DIR` | only if your Claude Code logs are not in `~/.claude/projects` |

## Privacy

Only what the dashboard shows is stored: titles, timestamps, counts, project or repo names.
Never conversation text, task descriptions, or code. Tokens live in `.env` and are never
rendered. Each connector requests the smallest permission that works.

## What I learned building it

- **Connector pattern.** `fetch()` talks to the network, `normalize()` is a pure function, `mock()` is
  the same shape faked. Every source, same three methods.
- **Identity matters more than schema.** Each connector must decide what counts as one activity
  and what its stable id is. Recurring Todoist tasks and resumed Claude Code sessions both bit me here.
- **Idempotent ingestion.** `INSERT ... ON CONFLICT DO NOTHING RETURNING id` means re-running is
  always safe and tells you what was actually new.
- **Timezones in SQL.** Rows are UTC; "today" is computed with `AT TIME ZONE` so it's *your* today.
- **One JSONB column beats six side tables** for an MVP. `metadata->>'difficulty'` in a `FILTER`
  clause does the rest.
- **Don't compare unlike units.** Commits, problems, tasks and hours don't belong on one bar chart.
  Compare each source with its own previous period instead.
- **Streamlit gotchas.** `st.markdown` runs HTML through Markdown (blank lines end the block);
  use `st.html`. Date axes with few points need explicit ticks and range.

## Not in V1 (and why)

- Google Calendar, Goodreads, Spotify: OAuth setup or Premium requirements that didn't fit one day.
- "Log in with GitHub" buttons: only worth it for a single hosted instance; for a clone-and-run app
  each person would need their own OAuth app, which is more setup than a token.
- Multi-user: the table has a nullable `user_id` ready for it, nothing else yet.
- Scheduled sync, WakaTime, Codeforces, Anki: good V2 candidates.
