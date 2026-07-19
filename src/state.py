"""Central shared state for the Atlas.

One coherent selection model drives the map, side panel, venue drawer, and
time controls. Every page reads the same keys from st.session_state.
"""
from __future__ import annotations

import streamlit as st

STATE_KEYS = {
    "mode": "place",            # "place" | "artist"
    "selected_artist": None,     # artist_id
    "selected_city": None,       # city_id
    "selected_venue": None,      # venue_id
    "time_mode": "all",          # "all" | "year" | "range"
    "year": None,                # single-year mode
    "start_year": None,          # range mode
    "end_year": None,
    "map_nonce": 0,              # bumped to discard stale map click selections
    "profile_artist": None,      # artist_id shown on the Artists page
}


def init_state(min_year: int, max_year: int) -> None:
    for key, default in STATE_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default
    if st.session_state.year is None:
        st.session_state.year = max_year
    if st.session_state.start_year is None:
        st.session_state.start_year = min_year
    if st.session_state.end_year is None:
        st.session_state.end_year = max_year
    st.session_state.data_min_year = min_year
    st.session_state.data_max_year = max_year


def bump_map_nonce() -> None:
    """Invalidate any click selection held by an existing map widget."""
    st.session_state.map_nonce += 1


def year_bounds() -> tuple[int, int]:
    """Active inclusive year window for the current time mode."""
    s = st.session_state
    if s.time_mode == "year":
        return s.year, s.year
    if s.time_mode == "range":
        return s.start_year, s.end_year
    return s.data_min_year, s.data_max_year


def select_city(city_id: int) -> None:
    if st.session_state.selected_city != city_id:
        st.session_state.selected_city = city_id
        st.session_state.selected_venue = None
        bump_map_nonce()


def clear_city() -> None:
    st.session_state.selected_city = None
    st.session_state.selected_venue = None
    bump_map_nonce()


def select_venue(venue_id: int) -> None:
    if st.session_state.selected_venue != venue_id:
        st.session_state.selected_venue = venue_id
        bump_map_nonce()


def clear_venue() -> None:
    st.session_state.selected_venue = None
    bump_map_nonce()


def select_artist(artist_id: int | None) -> None:
    """Switch into artist mode; incompatible place selections are cleared
    by the page after filtering (see prune_empty_selections)."""
    if st.session_state.selected_artist != artist_id:
        st.session_state.selected_artist = artist_id
        bump_map_nonce()


def set_mode(mode: str) -> None:
    if st.session_state.mode != mode:
        st.session_state.mode = mode
        if mode == "place":
            st.session_state.selected_artist = None
        bump_map_nonce()


def reset_all() -> None:
    for key, default in STATE_KEYS.items():
        if key not in ("map_nonce", "profile_artist"):
            st.session_state[key] = default
    st.session_state.year = st.session_state.data_max_year
    st.session_state.start_year = st.session_state.data_min_year
    st.session_state.end_year = st.session_state.data_max_year
    bump_map_nonce()


def prune_empty_selections(filtered_events) -> list[str]:
    """Clear selections that no longer match any event after filtering.

    Returns human-readable notes about what was cleared so the page can
    explain the change instead of failing silently.
    """
    notes: list[str] = []
    s = st.session_state
    if s.selected_venue is not None and s.selected_venue not in set(filtered_events.venue_id.dropna()):
        s.selected_venue = None
        notes.append("The selected venue has no shows in the current filter, so it was cleared.")
        bump_map_nonce()
    if s.selected_city is not None and s.selected_city not in set(filtered_events.city_id.dropna()):
        s.selected_city = None
        notes.append("The selected city has no shows in the current filter, so the map returned to all cities.")
        bump_map_nonce()
    return notes
