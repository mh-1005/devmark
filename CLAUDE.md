# CLAUDE.md

## Working style

- Explain what you're doing before and after implementing.
- Don't over-engineer.
- Prefer simple, readable code.
- Use the project's existing stack.
- Don't add dependencies unless necessary.
- Don't silently make major architectural decisions.
- After each milestone, stop and explain what changed.
- Teach the engineering concept behind important code.
- Don't generate huge amounts of code at once.
- Ask before making major scope changes.

## Project: Digital Life Dashboard (one-day MVP)

One user connects services, connectors pull a little activity data, it is normalized
into one `Activity` model, stored in PostgreSQL via SQLAlchemy, and shown in one Streamlit dashboard.

### Stack (fixed)
Python, uv, PostgreSQL, SQLAlchemy, Streamlit, Plotly, httpx, python-dotenv, Git.
No FastAPI, no React, no Docker/Redis/Celery/Airflow/Kubernetes, no cloud deploy, no heavy test infra.

### Unified activity model
Every source produces the same `Activity` shape (source, category, activity_type, title, timestamp, duration, metadata).
Source → category: GitHub→BUILD, LeetCode→LEARN, Google Calendar→TIME, Spotify→LISTEN, Goodreads→READ, Todoist→DO.

### Connector pattern
Each connector: `fetch()` → `normalize()` → list of `Activity`. Keep them isolated and small.
`USE_MOCK_DATA=true` switches to realistic mock data. If a real API is hard, say what blocks it, keep the interface, use mock, move on.
V1 integrations only: GitHub, LeetCode, Google Calendar, Spotify, Goodreads, Todoist.

### Architecture rules
Single local user operationally, but don't hardcode a personal identity; schema should allow a user/account link later.
Credentials in `.env` only; `.env.example` committed. Store only what the dashboard needs.
Use raw SQL for dashboard analytics where it makes the query clearer.

### Process
Build in milestones (Step 1 setup → Step 2 DB+model → Step 3 GitHub connector → Step 4 remaining connectors → dashboard polish → README).
After each milestone STOP and use the "STEP COMPLETE" format (What we built / Why / Files changed / How it works / Run this / Expected result / What I learned / Next).
Give 30-second practical explanations of concepts at the moment they are used. Small meaningful git commits.
Dashboard aesthetic: minimal, data-focused, slightly nerdy, modern. Numbers always come from the database.
