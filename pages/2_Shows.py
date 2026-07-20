"""Shows — the dependable searchable archive beneath the creative views."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.event_cards import render_archive_sections
from src.filters import bill_for, filter_events
from src.formatting import esc, fmt_date, place_line
from src.repository import artist_frame, event_frame
from src.state import init_state, select_city, select_venue, set_mode
from src.ui import inject_css, page_header

st.set_page_config(page_title="Shows · My Concert Atlas", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()
page_header()


@st.cache_data
def load_data():
    return event_frame(), artist_frame()


events, artist_events = load_data()
init_state(int(events.event_date.dt.year.min()), int(events.event_date.dt.year.max()))
s = st.session_state

st.markdown('<div class="eyebrow">The complete archive</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">SHOWS</div>', unsafe_allow_html=True)

multi_counts = artist_events.groupby("event_id").artist_id.nunique()

f1, f2, f3 = st.columns([1.4, 1, 1])
with f1:
    query = st.text_input("Search", placeholder="Artist, venue, city, or event title…")
with f2:
    lo, hi = s.data_min_year, s.data_max_year
    years = st.slider("Years", lo, hi, (lo, hi))
with f3:
    status = st.radio("Status", ["All", "Completed", "Upcoming"], horizontal=True)

g1, g2, g3, g4 = st.columns([1, 1, 1, 1])
with g1:
    artist_pick = st.selectbox("Artist", sorted(artist_events.display_name.unique()), index=None,
                               placeholder="Any artist")
with g2:
    city_pick = st.selectbox("City", sorted(events.city.dropna().unique()), index=None,
                             placeholder="Any city")
with g3:
    state_pick = st.selectbox("State / region", sorted(events.state_region.dropna().unique()),
                              index=None, placeholder="Any region")
with g4:
    multi_only = st.checkbox("Multi-artist bills only")

out = filter_events(events, artist_events, start_year=years[0], end_year=years[1])
if status == "Completed":
    out = out[out.is_upcoming == 0]
elif status == "Upcoming":
    out = out[out.is_upcoming == 1]
if artist_pick:
    ids = set(artist_events.loc[artist_events.display_name == artist_pick, "event_id"])
    out = out[out.event_id.isin(ids)]
if city_pick:
    out = out[out.city == city_pick]
if state_pick:
    out = out[out.state_region == state_pick]
if multi_only:
    out = out[out.event_id.map(multi_counts).fillna(1) > 1]
if query:
    ql = query.lower()
    text_cols = out[["event_title", "venue", "city", "state_region"]].astype(str)
    event_match = set(out[text_cols.apply(lambda c: c.str.lower().str.contains(ql, na=False)).any(axis=1)].event_id)
    artist_match = set(artist_events[artist_events.display_name.str.lower().str.contains(ql, na=False)].event_id)
    out = out[out.event_id.isin(event_match | artist_match)]

st.caption(f"{len(out):,} matching shows")

if len(out):
    # Inspect one show: full listed bill plus jumps to its venue, city, artists.
    ordered = out.sort_values("event_date", ascending=False)
    inspect = st.selectbox(
        "Inspect a show", ordered.event_id.tolist(), index=None,
        format_func=lambda i: (
            f"{fmt_date(ordered.loc[ordered.event_id == i, 'event_date'].iloc[0])} — "
            f"{ordered.loc[ordered.event_id == i, 'event_title'].iloc[0]}"
        ),
        placeholder="Inspect a show for its full bill and connections…",
        label_visibility="collapsed",
    )
    if inspect is not None:
        row = events[events.event_id == inspect].iloc[0]
        bill = bill_for(artist_events, int(inspect))
        chron = events.dropna(subset=["event_date"]).sort_values(["event_date", "event_id"]).reset_index(drop=True)
        pos = chron.index[chron.event_id == inspect]
        prev_row = chron.iloc[pos[0] - 1] if len(pos) and pos[0] > 0 else None
        next_row = chron.iloc[pos[0] + 1] if len(pos) and pos[0] < len(chron) - 1 else None
        neighbors = ""
        if prev_row is not None:
            neighbors += (f'<div class="muted small">Previous show: {fmt_date(prev_row.event_date)} — '
                          f'{esc(prev_row.event_title)} · {esc(prev_row.venue)}</div>')
        if next_row is not None:
            neighbors += (f'<div class="muted small">Next show: {fmt_date(next_row.event_date)} — '
                          f'{esc(next_row.event_title)} · {esc(next_row.venue)}</div>')
        st.markdown(
            f'<div class="mini-card"><div class="k">{fmt_date(row.event_date)}'
            f'{" · UPCOMING" if row.is_upcoming else ""}</div>'
            f'<div class="event-title">{esc(row.event_title)}</div>'
            f'<div class="muted small">{esc(row.venue)} · {esc(place_line(row.city, row.state_region))}</div>'
            f'<div class="event-bill">Listed bill, in recorded order: {" · ".join(esc(b) for b in bill)}</div>'
            f'{neighbors}</div>',
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("View venue on Atlas"):
                set_mode("place")
                select_city(int(row.city_id))
                select_venue(int(row.venue_id))
                st.switch_page("app.py")
        with b2:
            if st.button("View city on Atlas"):
                set_mode("place")
                select_city(int(row.city_id))
                st.switch_page("app.py")
        with b3:
            bill_rows = artist_events[artist_events.event_id == inspect].sort_values("billing_order")
            jump = st.selectbox("View an artist profile", bill_rows.artist_id.tolist(), index=None,
                                format_func=lambda i: bill_rows.loc[bill_rows.artist_id == i, "display_name"].iloc[0],
                                placeholder="View an artist profile…", label_visibility="collapsed")
            if jump is not None:
                s.profile_artist = int(jump)
                st.switch_page("pages/1_Artists.py")

    if "shows_limit" not in s:
        s.shows_limit = 60
    render_archive_sections(out, artist_events, limit=s.shows_limit)
    if len(out) > s.shows_limit:
        if st.button(f"Show {min(60, len(out) - s.shows_limit)} more"):
            s.shows_limit += 60
            st.rerun()

    with st.expander("Raw table and CSV download (secondary utility)"):
        table = out[["event_date", "event_title", "venue", "city", "state_region", "is_upcoming"]]
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button("Download CSV", table.to_csv(index=False), "shows_filtered.csv")
else:
    st.info("No shows match this combination. Loosen a filter to get back to the archive.")
