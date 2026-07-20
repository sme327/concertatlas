"""Artists — browsable directory plus deep-dive profiles.

The 30 most-seen artists get rich profiles; everyone else gets a clean
functional one. Profile numbers respect the universal time filter.
"""
from __future__ import annotations

import streamlit as st

from src.analytics import artist_summary
from src.components.artist_profile import render_profile
from src.components.time_controls import render_time_controls
from src.config import TOP_ARTIST_COUNT
from src.filters import filter_events
from src.formatting import esc, year_span
from src.repository import artist_frame, event_frame
from src.state import init_state, year_bounds
from src.ui import inject_css, page_header

st.set_page_config(page_title="Artists · My Concert Atlas", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()
page_header()


@st.cache_data
def load_data():
    return event_frame(), artist_frame()


events, artist_events = load_data()
init_state(int(events.event_date.dt.year.min()), int(events.event_date.dt.year.max()))
s = st.session_state

summary_all = artist_summary(artist_events)  # all-time ranking decides who gets a rich profile
top_ids = set(summary_all.head(TOP_ARTIST_COUNT).artist_id)
artist_names = dict(zip(summary_all.artist_id, summary_all.display_name))
artist_counts = dict(zip(summary_all.artist_id, summary_all.appearances))

st.markdown('<div class="eyebrow">Every recurring thread</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">ARTISTS</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1.6, 1.4])
with c1:
    ids = summary_all.artist_id.tolist()
    current = ids.index(s.profile_artist) if s.profile_artist in ids else None
    chosen = st.selectbox(
        "Find any artist", options=ids, index=current,
        format_func=lambda i: f"{artist_names[i]} — {artist_counts[i]}×",
        placeholder=f"Search all {len(ids):,} artists…",
    )
    if chosen is not None and chosen != s.profile_artist:
        s.profile_artist = chosen
        st.rerun()
with c2:
    st.markdown('<div class="eyebrow" style="padding-top:.4rem">Time window</div>', unsafe_allow_html=True)
    render_time_controls("artists")

st.markdown('<div class="eyebrow" style="margin-top:.6rem">The thirty most seen</div>', unsafe_allow_html=True)
top30 = summary_all.head(TOP_ARTIST_COUNT)
def _pick_from_pills():
    val = st.session_state.get("top30_pills")
    if val is not None:
        st.session_state.profile_artist = val


st.pills(
    "Top artists",
    options=top30.artist_id.tolist(),
    format_func=lambda i: f"{artist_names[i]} · {artist_counts[i]}",
    key="top30_pills",
    on_change=_pick_from_pills,
    label_visibility="collapsed",
)

start_year, end_year = year_bounds()

if s.profile_artist is None:
    # Directory view until an artist is chosen.
    st.divider()
    d1, d2 = st.columns([1, 1])
    with d1:
        search = st.text_input("Filter the directory", placeholder="Type part of a name…")
    with d2:
        min_appearances = st.slider("Minimum appearances", 1, 20, 1)
    directory = summary_all[summary_all.appearances >= min_appearances]
    if search:
        directory = directory[directory.display_name.str.contains(search, case=False, regex=False)]
    st.caption(f"{len(directory):,} artists — select one above (or via search) for the full profile.")
    rows = "".join(
        f'<div class="rank-row"><span>{esc(r.display_name)} '
        f'<span class="muted small">· {year_span(r.first_seen, r.latest_seen)} · '
        f'{int(r.cities)} cities</span></span><span class="n">{int(r.appearances)}</span></div>'
        for r in directory.head(120).itertuples()
    )
    st.markdown(rows, unsafe_allow_html=True)
    if len(directory) > 120:
        st.caption(f"… and {len(directory) - 120:,} more. Narrow the filter to see them.")
else:
    st.divider()
    artist_id = int(s.profile_artist)
    artist_filtered = filter_events(events, artist_events,
                                    start_year=start_year, end_year=end_year,
                                    artist_id=artist_id)
    render_profile(artist_id, artist_names.get(artist_id, "Unknown"),
                   artist_filtered, artist_events, rich=artist_id in top_ids)
    if artist_id not in top_ids:
        st.caption("Rich deep-dive profiles are reserved for the thirty most-seen artists; "
                   "this is the standard profile.")
    if st.button("See this artist on the Atlas map"):
        from src.state import select_artist, set_mode
        set_mode("artist")
        select_artist(artist_id)
        st.switch_page("app.py")
