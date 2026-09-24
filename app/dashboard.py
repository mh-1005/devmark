import streamlit as st

from app.database.queries import get_recent_activities

st.set_page_config(page_title="Digital Life", page_icon="◎", layout="wide")

st.title("My Digital Life")
st.caption("Everything I've been doing, in one place.")

activities = get_recent_activities()
st.subheader(f"{len(activities)} activities in the database")

for a in activities:
    st.write(f"**{a.timestamp.astimezone():%Y-%m-%d %H:%M}** · {a.source} · {a.activity_type} · {a.title}")
