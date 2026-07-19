"""The universal time control: ALL TIME | YEAR | RANGE.

Writes to the central state so every page recalculates from the same window.
"""
from __future__ import annotations

import streamlit as st

from src.state import bump_map_nonce

MODE_LABELS = {"all": "ALL TIME", "year": "YEAR", "range": "RANGE"}
LABEL_MODES = {v: k for k, v in MODE_LABELS.items()}


def render_time_controls(key_prefix: str = "tc") -> tuple[int, int]:
    """Render the control and return the active (start_year, end_year).

    Widgets are deliberately keyless: their identity derives from the
    central-state defaults, so they stay in sync when state changes
    programmatically or across pages.
    """
    s = st.session_state
    choice = st.segmented_control(
        "Time",
        options=list(MODE_LABELS.values()),
        default=MODE_LABELS[s.time_mode],
        label_visibility="collapsed",
    )
    new_mode = LABEL_MODES.get(choice, s.time_mode)
    if new_mode != s.time_mode:
        s.time_mode = new_mode
        bump_map_nonce()

    lo, hi = s.data_min_year, s.data_max_year
    if s.time_mode == "year":
        year = st.slider("Year", lo, hi, s.year)
        if year != s.year:
            s.year = year
            bump_map_nonce()
        return s.year, s.year
    if s.time_mode == "range":
        start, end = st.slider("Years", lo, hi, (s.start_year, s.end_year))
        if (start, end) != (s.start_year, s.end_year):
            s.start_year, s.end_year = start, end
            bump_map_nonce()
        return start, end
    return lo, hi
