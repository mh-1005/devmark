import html
import os
from datetime import date, datetime, time, timedelta

import plotly.graph_objects as go
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from app.config import save_env
from app.connectors import ALL_CONNECTORS
from app.connectors.base import mock_mode_enabled
from app.database import queries as q
from app.services.ingestion import ingest

APP_NAME = "DEVMARK"
TAGLINE = "Make your work visible."

RANGES = {"Today": 1, "7 days": 7, "30 days": 30, "All time": None}
PALETTES = {
    "dark": dict(bg="#0f1218", surface="#161a22", surface2="#1e232d", line="#2a3040", muted="#3a4152",
                 text="#e8ebf1", text2="#aab2c2", text3="#6f788a", mock="#f5b458", mock_bg="#2a2114",
                 BUILD="#3987e5", LEARN="#d95926", DO="#199e70", ASSIST="#c98500"),
    "light": dict(bg="#f4f5f7", surface="#ffffff", surface2="#eceef2", line="#e1e4ea", muted="#c9ced8",
                  text="#14171c", text2="#4d5563", text3="#8a93a3", mock="#b45309", mock_bg="#fff4e0",
                  BUILD="#2a78d6", LEARN="#eb6834", DO="#1baf7a", ASSIST="#eda100"),
}


def theme_type() -> str:
    """"light" or "dark", whichever the viewer chose in Streamlit's ⋮ → Settings (or their system).

    On a session's first run Streamlit does not know the theme yet and reports None. We rerun
    once (a few ms) so the second run has the real value; without this, every first load would
    render in the fallback colour.
    """
    try:
        kind = st.context.theme.type
    except Exception:  # noqa: BLE001  (not inside a Streamlit session, e.g. tests)
        return "dark"
    if kind is None and get_script_run_ctx() is not None and not st.session_state.get("_theme_probe"):
        st.session_state["_theme_probe"] = True
        st.rerun()
    return kind or "dark"


T = PALETTES[theme_type()]
COLOR = {cat: T[cat] for cat in ("BUILD", "LEARN", "DO", "ASSIST")}
SOURCE_LABEL = {"github": "GitHub", "leetcode": "LeetCode", "todoist": "Todoist", "claude_code": "Claude Code"}

st.set_page_config(page_title=APP_NAME, page_icon="◎", layout="wide")

st.html(f"""
<style>
:root {{ {" ".join(f"--{k}: {v};" for k, v in T.items())} }}
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap");
html, body, .stApp {{ font-family: "IBM Plex Sans", system-ui, sans-serif; }}
/* Streamlit draws its icons with a ligature font; keep our font away from them. */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {{ font-family: "Material Symbols Rounded" !important; }}
.block-container {{ max-width: 1140px; padding-top: 4rem; }}
.mono {{ font-family: "JetBrains Mono", ui-monospace, monospace; }}
.label {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--text3); font-weight: 500; }}

.hdr {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap;
       border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 14px; }}
.hdr h1 {{ margin: 0; font-size: 28px; font-weight: 600; font-family: "JetBrains Mono", monospace; }}
.hdr h1 span {{ color: var(--text3); font-weight: 400; }}
.hdr p {{ margin: 4px 0 0; color: var(--text2); font-size: 14px; }}
.hdr .right {{ text-align: right; display: grid; gap: 6px; justify-items: end; }}
.hdr .date {{ font-size: 13px; color: var(--text2); font-family: "JetBrains Mono", monospace; }}
.pill {{ font-size: 11px; padding: 3px 8px; border-radius: 4px; background: var(--mock_bg); color: var(--mock); font-weight: 600; letter-spacing: .04em; }}

.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 8px 0 18px; }}
.tile {{ background: var(--surface); border: 1px solid var(--line); border-top: 3px solid var(--c); border-radius: 8px; padding: 14px 16px 12px; display: grid; gap: 6px; }}
.tile .top {{ display: flex; justify-content: space-between; align-items: center; }}
.tile .src {{ font-size: 12px; color: var(--text3); }}
.tile .val {{ font-size: 30px; font-weight: 600; line-height: 1.1; letter-spacing: -.02em; font-family: "JetBrains Mono", monospace; }}
.tile .val small {{ font-size: 16px; color: var(--text3); }}
.tile .sub {{ font-size: 12px; color: var(--text2); }}

.panel {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
.panel h2 {{ margin: 0 0 12px; font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; }}
.panel h2 span {{ font-weight: 400; color: var(--text3); font-size: 12px; }}
.day {{ margin-top: 16px; }}
.day .label {{ margin-bottom: 6px; }}
.ev {{ display: grid; grid-template-columns: 52px 10px 1fr; gap: 10px; align-items: baseline; padding: 6px 0; border-top: 1px solid var(--line); }}
.ev:first-of-type {{ border-top: 0; }}
.ev .t {{ font-size: 12px; color: var(--text3); font-family: "JetBrains Mono", monospace; }}
.ev .d {{ width: 8px; height: 8px; border-radius: 50%; background: var(--c); align-self: center; }}
.ev .title {{ font-weight: 500; font-size: 14px; }}
.ev .meta {{ font-size: 12px; color: var(--text3); }}
.ev .meta b {{ color: var(--text2); font-weight: 500; }}
.hbar {{ display: grid; grid-template-columns: 90px 1fr 36px; gap: 10px; align-items: center; font-size: 12px; padding: 4px 0; }}
.hbar .bar {{ height: 8px; border-radius: 4px; background: var(--surface2); overflow: hidden; }}
.hbar .bar i {{ display: block; height: 100%; border-radius: 4px; background: var(--c); }}
.hbar .v {{ text-align: right; color: var(--text2); font-family: "JetBrains Mono", monospace; }}
.ptitle {{ font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; margin-bottom: 4px; }}
.ptitle span {{ font-weight: 400; color: var(--text3); font-size: 12px; }}
.hm {{ display: grid; grid-template-columns: 34px repeat(12, 1fr); gap: 3px; align-items: center; }}
.hm .rl {{ font-size: 11px; color: var(--text3); font-family: "JetBrains Mono", monospace; }}
.hm .c {{ display: block; height: 14px; border-radius: 3px; background: var(--surface2); }}
.hm .c.future {{ background: transparent; }}
.hm .wl {{ font-size: 10px; color: var(--text3); font-family: "JetBrains Mono", monospace; padding-top: 4px; }}
.legend {{ display: flex; gap: 14px; font-size: 11px; color: var(--text3); margin-top: 10px; }}
.legend i {{ display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }}
.cmp {{ display: grid; grid-template-columns: 90px 1fr 120px; gap: 10px; align-items: center; font-size: 12px; padding: 5px 0; }}
.cmp .bars {{ display: grid; gap: 3px; }}
.cmp .bar {{ height: 7px; border-radius: 4px; background: var(--surface2); overflow: hidden; }}
.cmp .bar i {{ display: block; height: 100%; border-radius: 4px; background: var(--c); }}
.cmp .bar.prev i {{ background: var(--muted); }}
.cmp .v {{ text-align: right; color: var(--text); font-family: "JetBrains Mono", monospace; }}
.cmp .v em {{ display: block; font-style: normal; color: var(--text3); font-size: 11px; }}
.acct {{ display: grid; grid-template-columns: 10px 1fr; gap: 8px; align-items: center; font-size: 13px; padding: 6px 0; border-top: 1px solid var(--line); }}
.acct:first-of-type {{ border-top: 0; }}
.acct .s {{ width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }}
.acct .s.on {{ background: var(--DO); }}
.acct .s.mock {{ background: var(--mock); }}
.acct small {{ display: block; color: var(--text3); font-size: 11px; }}
.sync {{ font-size: 11px; color: var(--text3); line-height: 1.6; font-family: "JetBrains Mono", monospace; }}
.tile.off .val {{ color: var(--text3); }}
.empty {{ color: var(--text3); font-size: 13px; padding: 24px 0; text-align: center; }}
@media (max-width: 800px) {{ .tiles {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
""")

# ---- auto sync -------------------------------------------------------------

SYNC_EVERY_SECONDS = 5 * 60


@st.cache_data(ttl=SYNC_EVERY_SECONDS, show_spinner="Syncing…")
def auto_sync() -> list[dict]:
    """Runs ingest at most once per SYNC_EVERY_SECONDS, shared by every open tab.
    The cache is the throttle: while a result is cached, this returns it without touching any API."""
    return ingest([cls() for cls in ALL_CONNECTORS])


# ---- sidebar: accounts, connect, sync -------------------------------------

connectors = {cls.source: cls() for cls in ALL_CONNECTORS}  # fresh instances read the current .env
mock = mock_mode_enabled()
connected = {src: mock or c.is_configured() for src, c in connectors.items()}
active = [src for src, ok in connected.items() if ok]          # only these sources appear anywhere
SOURCES = {"All": None, **{SOURCE_LABEL[src]: src for src in active}}

with st.sidebar:
    st.html('<div class="ptitle">Accounts</div>' + "".join(
        f'<div class="acct"><i class="s {"mock" if mock else "on" if c.is_configured() else ""}"></i>'
        f'<div>{SOURCE_LABEL[src]}<small>{"mock data" if mock else c.status()}</small></div></div>'
        for src, c in connectors.items()
    ))

    with st.expander("Connect accounts", expanded=not all(c.is_configured() for c in connectors.values())):
        with st.form("connect", border=False):
            gh_token = st.text_input("GitHub token", type="password")
            gh_user = st.text_input("GitHub username", value=os.getenv("GITHUB_USERNAME", ""))
            lc_user = st.text_input("LeetCode username", value=os.getenv("LEETCODE_USERNAME", ""))
            td_token = st.text_input("Todoist token", type="password")
            if st.form_submit_button("Save", type="primary"):
                typed = {"GITHUB_TOKEN": gh_token, "GITHUB_USERNAME": gh_user, "LEETCODE_USERNAME": lc_user, "TODOIST_API_TOKEN": td_token}
                save_env({k: v.strip() for k, v in typed.items() if v.strip()})  # blank = leave as is
                st.session_state["force_sync"] = True  # new token → sync right away
                st.rerun()
        st.caption("Saved to .env on this machine. Tokens are never shown again.")

    if st.button("⟳  Sync now", width="stretch"):
        st.session_state["force_sync"] = True
        st.rerun()

forced = st.session_state.pop("force_sync", False)
if forced:
    auto_sync.clear()
sync_results = auto_sync()
if forced:
    errors = [f"{SOURCE_LABEL[r['source']]}: {r['error'][:80]}" for r in sync_results if r["mode"] == "error"]
    new = sum(r["inserted"] for r in sync_results)
    st.toast(f"Synced · {new} new marks" if not errors else "Sync finished with errors: " + "; ".join(errors))

# ---- header ---------------------------------------------------------------

mock_pill = '<span class="pill">● INCLUDES MOCK DATA</span>' if (mock or q.has_mock_rows()) else ""
st.html(f"""
<div class="hdr">
  <div><h1>{APP_NAME}</h1><p>{TAGLINE}</p></div>
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
scope = source or active   # one source, or every connected source
days = RANGES[range_label or "7 days"]

# ---- tiles ----------------------------------------------------------------

b = q.build_summary(days, scope)
l = q.learn_summary(days, scope)
d = q.do_summary(days, scope)
a = q.assist_summary(days, scope)


def tile(cat: str, src: str, value: str, sub: str, off: bool = False) -> str:
    return (f'<div class="tile{" off" if off else ""}" style="--c:{COLOR[cat]}"><div class="top"><span class="label">{cat.title()}</span>'
            f'<span class="src">{src}</span></div><div class="val">{value}</div><div class="sub">{sub}</div></div>')


def off_tile(cat: str, src: str) -> str:
    return tile(cat, src, "—", "Not connected · add it in the sidebar", off=True)




tiles = {
    "github": tile("BUILD", "GitHub", str(b["commits"]), f'commits · {b["prs"]} pull requests · {b["repos"]} repos') if connected["github"] else off_tile("BUILD", "GitHub"),
    "leetcode": tile("LEARN", "LeetCode", str(l["problems"]), f'problems · {l["easy"]} easy · {l["medium"]} medium · {l["hard"]} hard') if connected["leetcode"] else off_tile("LEARN", "LeetCode"),
    "todoist": tile("DO", "Todoist", str(d["tasks"]), f'tasks completed · {d["projects"]} projects') if connected["todoist"] else off_tile("DO", "Todoist"),
    "claude_code": tile("ASSIST", "Claude Code", f'{a["hours"]:.1f}<small>h</small>', f'{a["sessions"]} sessions · {a["projects"]} projects · {a["prompts"]} prompts') if connected["claude_code"] else off_tile("ASSIST", "Claude Code"),
}
shown = [tiles[source]] if source else list(tiles.values())
st.html('<div class="tiles">' + "".join(shown) + "</div>")

# ---- charts ---------------------------------------------------------------

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans, sans-serif", color=T["text2"], size=12),
    margin=dict(l=0, r=0, t=8, b=0), showlegend=False, hoverlabel=dict(bgcolor=T["surface2"], font_color=T["text"]),
)
NO_MODEBAR = {"displayModeBar": False}


CATEGORY_SOURCE = {"BUILD": "GitHub", "LEARN": "LeetCode", "DO": "Todoist", "ASSIST": "Claude Code"}
SOURCE_CATEGORY = {"github": "BUILD", "leetcode": "LEARN", "todoist": "DO", "claude_code": "ASSIST"}


def heatmap_html(source) -> str:
    """Contribution grid for the last 12 weeks. Cell color = the category that dominated the day,
    shade = how much happened, hover = the full breakdown."""
    today = date.today()
    start = today - timedelta(days=today.weekday() + 7 * 11)  # Monday, 11 weeks back
    per_day: dict[date, dict[str, int]] = {}
    for r in q.per_day(None, source):
        if r["day"] >= start:
            per_day.setdefault(r["day"], {})[r["category"]] = r["n"]
    busiest = max((sum(c.values()) for c in per_day.values()), default=1)

    cells = []
    for dow, row_label in enumerate(["Mon", "", "Wed", "", "Fri", "", "Sun"]):
        cells.append(f'<span class="rl">{row_label}</span>')
        for week in range(12):
            day = start + timedelta(weeks=week, days=dow)
            if day > today:
                cells.append('<i class="c future"></i>')
                continue
            cats = per_day.get(day)
            if not cats:
                cells.append(f'<i class="c" title="{day:%a %d %b} · no marks"></i>')
                continue
            total = sum(cats.values())
            dominant = max(cats, key=cats.get)
            shade = 0.35 + 0.65 * total / busiest
            detail = ", ".join(f"{n} {CATEGORY_SOURCE[c]}" for c, n in sorted(cats.items(), key=lambda kv: -kv[1]))
            cells.append(f'<i class="c" style="background:{COLOR[dominant]};opacity:{shade:.2f}" title="{day:%a %d %b} · {detail}"></i>')
    cells.append('<span></span>')
    for week in range(12):
        monday = start + timedelta(weeks=week)
        cells.append(f'<span class="wl">{monday:%d %b}</span>' if week % 2 == 0 else '<span class="wl"></span>')
    in_play = [SOURCE_CATEGORY[s] for s in ([source] if isinstance(source, str) else source)]
    legend = "".join(f'<span><i style="background:{COLOR[c]}"></i>{CATEGORY_SOURCE[c]}</span>' for c in in_play)
    return f'<div class="hm">{"".join(cells)}</div><div class="legend">{legend}</div>'


def per_day_chart(days, source) -> go.Figure | None:
    """Stacked bars, one per local day, one segment per category."""
    rows = q.per_day(days, source)
    if not rows:
        return None
    end = date.today()
    start = end - timedelta(days=(days or 1) - 1) if days else min(r["day"] for r in rows)
    span = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    fig = go.Figure()
    for cat, color in COLOR.items():
        by_day = {r["day"]: r["n"] for r in rows if r["category"] == cat}
        if by_day:
            fig.add_bar(name=cat.title(), x=span, y=[by_day.get(d, 0) for d in span], marker_color=color,
                        hovertemplate="%{x|%a %d %b} · %{y} " + cat.lower() + "<extra></extra>")
    fig.update_layout(**PLOT_LAYOUT, barmode="stack", bargap=0.25, height=220)
    # Explicit ticks: Plotly would otherwise zoom a short window to hours and repeat the same date label.
    pad = timedelta(hours=12)
    fig.update_xaxes(showgrid=False, tickformat="%d %b", range=[datetime.combine(start, time.min) - pad, datetime.combine(end, time.min) + pad],
                     tickvals=span if len(span) <= 14 else None)
    fig.update_yaxes(gridcolor=T["line"], zeroline=False, dtick=1 if max(r["n"] for r in rows) < 6 else None)
    return fig


def bar_list(rows: list[tuple[str, int, str]]) -> str:
    """Horizontal bar list rendered as HTML. rows = [(label, value, color), ...]"""
    if not rows:
        return '<div class="empty">Nothing in this window.</div>'
    top = max(v for _, v, _ in rows) or 1
    return "".join(
        f'<div class="hbar" style="--c:{c}"><span>{label}</span><div class="bar"><i style="width:{100 * v / top:.0f}%"></i></div><span class="v">{v}</span></div>'
        for label, v, c in rows
    )


st.html('<div class="panel"><h2>Last 12 weeks <span>one cell per day, coloured by the kind of mark that led</span></h2>' + heatmap_html(scope) + '</div>')


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


left, right = st.columns([1.3, 1], gap="medium")

with right:
    with st.container(border=True):
        st.html(f'<div class="ptitle">Activity per day <span>{range_label or "7 days"}</span></div>')
        fig = per_day_chart(days, scope)
        if fig:
            st.plotly_chart(fig, config=NO_MODEBAR)
        else:
            st.html('<div class="empty">Nothing in this window.</div>')

    WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = {r["dow"]: r["n"] for r in q.by_weekday(days, scope)}
    st.html('<div class="panel"><h2>Which days I actually work <span>' + (range_label or "7 days") + '</span></h2>'
            + bar_list([(WEEKDAYS[i - 1], dow.get(i, 0), T["text2"]) for i in range(1, 8)] if dow else []) + '</div>')

    UNIT = {"github": "commits", "leetcode": "solved", "todoist": "done", "claude_code": "sessions"}
    if days is None:
        st.html('<div class="panel"><h2>Where it came from <span>all time</span></h2>'
                + bar_list([(SOURCE_LABEL.get(r["source"], r["source"]), r["n"], COLOR[r["category"]]) for r in q.by_source(None, scope)]) + '</div>')
    else:
        cmp_rows = []
        for r in q.source_comparison(days, scope):
            top = max(r["current"], r["previous"]) or 1
            arrow = "▲" if r["current"] > r["previous"] else "▼" if r["current"] < r["previous"] else "="
            cmp_rows.append(
                f'<div class="cmp" style="--c:{COLOR[r["category"]]}"><span>{SOURCE_LABEL[r["source"]]}</span>'
                f'<div class="bars"><div class="bar"><i style="width:{100 * r["current"] / top:.0f}%"></i></div></div>'
                f'<span class="v">{r["current"]} {UNIT[r["source"]]}<em>{arrow} was {r["previous"]}</em></span></div>'
            )
        st.html(f'<div class="panel"><h2>Compared to the previous {range_label.lower()}</h2>'
                + ("".join(cmp_rows) or '<div class="empty">Nothing in either window.</div>') + '</div>')

rows = q.timeline(days, scope)
parts = ['<div class="panel"><h2>Marks <span>every source, newest first</span></h2>']
if not rows:
    parts.append('<div class="empty">No marks in this window. Try a wider range, or sync.</div>')
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
with left:
    st.html("".join(parts))
