import html
from datetime import date, timedelta

import streamlit as st

from app.connectors.base import mock_mode_enabled
from app.database import queries as q

APP_NAME = "devlog"
TAGLINE = "What I built, learned, finished, and asked for help with."

SOURCES = {"All": None, "GitHub": "github", "LeetCode": "leetcode", "Todoist": "todoist", "Claude Code": "claude_code"}
RANGES = {"Today": 1, "7 days": 7, "30 days": 30, "All time": None}
COLOR = {"BUILD": "#3987e5", "LEARN": "#d95926", "DO": "#199e70", "ASSIST": "#c98500"}
SOURCE_LABEL = {"github": "GitHub", "leetcode": "LeetCode", "todoist": "Todoist", "claude_code": "Claude Code"}

st.set_page_config(page_title=APP_NAME, page_icon="◎", layout="wide")

st.html("""
<style>
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap");
html, body, [class*="st-"] { font-family: "IBM Plex Sans", system-ui, sans-serif; }
.block-container { max-width: 1140px; padding-top: 2rem; }
.mono { font-family: "JetBrains Mono", ui-monospace, monospace; }
.label { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #6f788a; font-weight: 500; }

.hdr { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap;
       border-bottom: 1px solid #2a3040; padding-bottom: 14px; margin-bottom: 14px; }
.hdr h1 { margin: 0; font-size: 28px; font-weight: 600; font-family: "JetBrains Mono", monospace; }
.hdr h1 span { color: #6f788a; font-weight: 400; }
.hdr p { margin: 4px 0 0; color: #aab2c2; font-size: 14px; }
.hdr .right { text-align: right; display: grid; gap: 6px; justify-items: end; }
.hdr .date { font-size: 13px; color: #aab2c2; font-family: "JetBrains Mono", monospace; }
.pill { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: #2a2114; color: #f5b458; font-weight: 600; letter-spacing: .04em; }

.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 8px 0 18px; }
.tile { background: #161a22; border: 1px solid #2a3040; border-top: 3px solid var(--c); border-radius: 8px; padding: 14px 16px 12px; display: grid; gap: 6px; }
.tile .top { display: flex; justify-content: space-between; align-items: center; }
.tile .src { font-size: 12px; color: #6f788a; }
.tile .val { font-size: 30px; font-weight: 600; line-height: 1.1; letter-spacing: -.02em; font-family: "JetBrains Mono", monospace; }
.tile .val small { font-size: 16px; color: #6f788a; }
.tile .sub { font-size: 12px; color: #aab2c2; }

.panel { background: #161a22; border: 1px solid #2a3040; border-radius: 8px; padding: 16px; }
.panel h2 { margin: 0 0 12px; font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; }
.panel h2 span { font-weight: 400; color: #6f788a; font-size: 12px; }
.day { margin-top: 16px; }
.day .label { margin-bottom: 6px; }
.ev { display: grid; grid-template-columns: 52px 10px 1fr; gap: 10px; align-items: baseline; padding: 6px 0; border-top: 1px solid #2a3040; }
.ev:first-of-type { border-top: 0; }
.ev .t { font-size: 12px; color: #6f788a; font-family: "JetBrains Mono", monospace; }
.ev .d { width: 8px; height: 8px; border-radius: 50%; background: var(--c); align-self: center; }
.ev .title { font-weight: 500; font-size: 14px; }
.ev .meta { font-size: 12px; color: #6f788a; }
.ev .meta b { color: #aab2c2; font-weight: 500; }
.empty { color: #6f788a; font-size: 13px; padding: 24px 0; text-align: center; }
@media (max-width: 800px) { .tiles { grid-template-columns: repeat(2, 1fr); } }
</style>
""")

# ---- header ---------------------------------------------------------------

mock_pill = '<span class="pill">● MOCK DATA</span>' if mock_mode_enabled() else ""
st.html(f"""
<div class="hdr">
  <div><h1>{APP_NAME}<span>_</span></h1><p>{TAGLINE}</p></div>
  <div class="right"><div class="date">{date.today():%a %d %b %Y}</div>{mock_pill}</div>
</div>
""")

# ---- filters --------------------------------------------------------------

left, right = st.columns([3, 2])
with left:
    source_label = st.pills("Source", list(SOURCES), default="All", label_visibility="collapsed")
with right:
    range_label = st.pills("Range", list(RANGES), default="7 days", label_visibility="collapsed")

source = SOURCES[source_label or "All"]
days = RANGES[range_label or "7 days"]

# ---- tiles ----------------------------------------------------------------

b = q.build_summary(days, source)
l = q.learn_summary(days, source)
d = q.do_summary(days, source)
a = q.assist_summary(days, source)


def tile(cat: str, src: str, value: str, sub: str) -> str:
    return (f'<div class="tile" style="--c:{COLOR[cat]}"><div class="top"><span class="label">{cat.title()}</span>'
            f'<span class="src">{src}</span></div><div class="val">{value}</div><div class="sub">{sub}</div></div>')


st.html('<div class="tiles">' + "".join([
    tile("BUILD", "GitHub", str(b["commits"]), f'commits · {b["prs"]} pull requests · {b["repos"]} repos'),
    tile("LEARN", "LeetCode", str(l["problems"]), f'problems · {l["easy"]} easy · {l["medium"]} medium · {l["hard"]} hard'),
    tile("DO", "Todoist", str(d["tasks"]), f'tasks completed · {d["projects"]} projects'),
    tile("ASSIST", "Claude Code", f'{a["hours"]:.1f}<small>h</small>', f'{a["sessions"]} sessions · {a["projects"]} projects · {a["prompts"]} prompts'),
]) + "</div>")

# ---- timeline -------------------------------------------------------------


def describe(row: dict) -> str:
    """Second line of a timeline entry: source plus the one or two details that matter."""
    m = row["metadata"] or {}
    src = SOURCE_LABEL.get(row["source"], row["source"])
    match row["source"]:
        case "github":
            kind = "pull request" if row["activity_type"] == "pull_request" else "commit"
            return f"<b>{src}</b> · {kind} · {m.get('repo', '')}"
        case "leetcode":
            return f"<b>{src}</b> · {m.get('difficulty', '')} · {m.get('lang', '')}"
        case "todoist":
            return f"<b>{src}</b> · completed · {m.get('project', '')}"
        case "claude_code":
            mins = (row["duration_seconds"] or 0) // 60
            return f"<b>{src}</b> · {mins} min · {m.get('user_messages', 0)} prompts"
    return f"<b>{src}</b>"


def day_label(day: date) -> str:
    today = date.today()
    prefix = "Today · " if day == today else "Yesterday · " if day == today - timedelta(days=1) else ""
    return f"{prefix}{day:%a %d %b}"


rows = q.timeline(days, source)
parts = ['<div class="panel"><h2>Timeline <span>all sources, newest first</span></h2>']
if not rows:
    parts.append('<div class="empty">Nothing in this window. Try a wider range, or run <code>uv run python -m scripts.ingest</code>.</div>')
current_day = None
for r in rows:
    day = r["local_ts"].date()
    if day != current_day:
        if current_day is not None:
            parts.append("</div>")  # close the previous day
        parts.append(f'<div class="day"><div class="label">{day_label(day)}</div>')
        current_day = day
    parts.append(
        f'<div class="ev" style="--c:{COLOR[r["category"]]}"><span class="t">{r["local_ts"]:%H:%M}</span><i class="d"></i>'
        f'<div><div class="title">{html.escape(r["title"])}</div><div class="meta">{describe(r)}</div></div></div>'
    )
if current_day is not None:
    parts.append("</div>")
parts.append("</div>")
st.html("".join(parts))
