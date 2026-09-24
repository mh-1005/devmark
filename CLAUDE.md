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
Source → category: GitHub→BUILD, LeetCode→LEARN, Todoist→DO. (More sources may be added; see decisions below.)

### Connector pattern
Each connector: `fetch()` → `normalize()` → list of `Activity`. Keep them isolated and small.
`USE_MOCK_DATA=true` switches to realistic mock data. If a real API is hard, say what blocks it, keep the interface, use mock, move on.
V1 integrations: GitHub, LeetCode, Todoist.
Decision (2026-09-24): Google Calendar, Goodreads and Spotify are DROPPED from V1 entirely (Spotify now requires Premium for dev apps). No connectors, no mocks for them.
Project may be renamed and refocused on productivity / computer science; name TBD.

### Architecture rules
Single local user operationally, but don't hardcode a personal identity; schema should allow a user/account link later.
Credentials in `.env` only; `.env.example` committed. Store only what the dashboard needs.
Use raw SQL for dashboard analytics where it makes the query clearer.

### Process
Build in milestones (Step 1 setup → Step 2 DB+model → Step 3 GitHub connector → Step 4 remaining connectors → dashboard polish → README).
After each milestone STOP and use the "STEP COMPLETE" format (What we built / Why / Files changed / How it works / Run this / Expected result / What I learned / Next).
Give 30-second practical explanations of concepts at the moment they are used. Small meaningful git commits.
Dashboard aesthetic: minimal, data-focused, slightly nerdy, modern. Numbers always come from the database.

### Learning notes
After each step, write the "What I learned" content to `learnings/step-N.md` (git-ignored). Keep the STEP COMPLETE report in chat short on that section and point to the file.

### Overview
Here's the mock: https://claude.ai/artifact/WweAfUb1QADKhiKPydfzYJ

Every number on it is fake. The point is layout, hierarchy, and what each section is for. It adapts to your light or dark theme.

What's on the page, top to bottom

Header. Project name, one-line tagline, today's date, and a "MOCK DATA" pill that only shows when mock mode is on.
Filters. Source chips and a time range. In Streamlit these become a segmented control and a radio row in the same position.
Four tiles. One per category. Big number, a sub-line with the breakdown, and a tiny 14-day bar strip so you can see the shape at a glance.
Timeline. The main feature. All four sources merged, grouped by day, newest first. Time, colored dot for the source, title, then source and detail in the second line.
Three charts. Activity per day stacked by category, which weekdays you actually work, and where activity came from. Each answers one question.
Explainer cards. What each source contributes. This section is for you now and won't be on the real dashboard.
What each source tells you

GitHub → Build. What you shipped. Commits and PRs with the repo. Answers "am I shipping, and on what?"
LeetCode → Learn. What you practiced. Each accepted solution with difficulty and language. Answers "am I practicing, and am I pushing past easy?"
Todoist → Do. What you finished. Completed tasks with project and labels. Answers "am I closing things, and is it uni, projects, or life?"
Claude Code → Assist. When and where you used AI. One row per session with duration and message count, never the conversation text. Answers "how much of my work is AI-assisted, and on which projects?"
Colors. The four category colors come from a colorblind-safe palette with validated light and dark variants. The same four colors carry through tiles, timeline dots, chips, and charts, so a color always means the same source.