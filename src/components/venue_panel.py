"""The venue detail drawer shown beside the map."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics import venue_artist_constellation
from src.components.event_cards import render_ticket_list
from src.formatting import esc, place_line, year_of
from src.state import clear_venue, select_artist, set_mode
from src.ui import constellation_html, year_strip_html


def render_venue_panel(
    venue_row: pd.Series,
    filtered: pd.DataFrame,
    artist_events: pd.DataFrame,
) -> None:
    """venue_row comes from analytics.venue_aggregates for the active filter."""
    venue_id = int(venue_row.venue_id)
    venue_events = filtered[filtered.venue_id == venue_id]
    first_year, latest_year = int(year_of(venue_row.first_date)), int(year_of(venue_row.latest_date))
    active_years = set(venue_events.event_date.dt.year.dropna().astype(int))

    st.markdown(
        f'<div class="side-panel">'
        f'<div class="panel-title">{esc(venue_row.venue)}</div>'
        f'<div class="panel-sub">{esc(place_line(venue_row.city, venue_row.state_region))}</div>'
        f'<div class="stat-line"><span>Shows</span><b>{int(venue_row.shows)}</b></div>'
        f'<div class="stat-line"><span>Artists encountered</span><b>{int(venue_row.artists)}</b></div>'
        f'<div class="stat-line"><span>First visit</span><b>{first_year}</b></div>'
        f'<div class="stat-line"><span>Latest visit</span><b>{latest_year}</b></div>'
        f'{year_strip_html(first_year, latest_year, active_years)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    constellation = venue_artist_constellation(filtered, artist_events, venue_id)
    st.markdown('<div class="eyebrow" style="margin-top:.8rem">Artists in this room</div>', unsafe_allow_html=True)
    st.markdown(constellation_html(constellation), unsafe_allow_html=True)

    if len(constellation):
        names = constellation.display_name.tolist()
        chosen = st.selectbox("Follow an artist from this room", names, index=None,
                              placeholder="Follow an artist from this room…",
                              key=f"venue_follow_{venue_id}", label_visibility="collapsed")
        if chosen:
            artist_id = int(constellation.loc[constellation.display_name == chosen, "artist_id"].iloc[0])
            set_mode("artist")
            select_artist(artist_id)
            clear_venue()
            st.rerun()

    with st.expander(f"All {int(venue_row.shows)} shows here, chronologically"):
        render_ticket_list(venue_events, artist_events, limit=100, newest_first=False,
                           variant="journey_compact")

    st.button("Close venue", on_click=clear_venue, key=f"close_venue_{venue_id}")
