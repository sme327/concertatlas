"""The universal time control: ALL TIME | TIMELINE.

One timeline replaces the old Year/Range pair: it opens on a single year
(both handles together) and dragging a handle naturally expands it into a
range. ALL TIME remains the shortcut. Writes to central state so every page
recalculates from the same window.
"""
from __future__ import annotations

import streamlit as st

from src.state import bump_map_nonce

MODE_LABELS = {"all": "ALL TIME", "range": "TIMELINE"}
LABEL_MODES = {v: k for k, v in MODE_LABELS.items()}


def render_time_controls(key_prefix: str = "tc") -> tuple[int, int]:
    """Render the control and return the active (start_year, end_year).

    Widgets are deliberately keyless: their identity derives from the
    central-state defaults, so they stay in sync when state changes
    programmatically (e.g. clicking a histogram bar) or across pages.
    """
    s = st.session_state
    if s.time_mode == "year":            # migrate any legacy single-year state
        s.time_mode = "range"
        s.start_year = s.end_year = s.year
    choice = st.segmented_control(
        "Time",
        options=list(MODE_LABELS.values()),
        default=MODE_LABELS[s.time_mode],
        label_visibility="collapsed",
    )
    new_mode = LABEL_MODES.get(choice, s.time_mode)
    if new_mode != s.time_mode:
        s.time_mode = new_mode
        if new_mode == "range" and s.start_year == s.data_min_year and s.end_year == s.data_max_year:
            # Entering the timeline starts on one year; drag to widen.
            s.start_year = s.end_year = s.year
        bump_map_nonce()

    lo, hi = s.data_min_year, s.data_max_year
    if s.time_mode == "range":
        start, end = st.slider("Timeline", lo, hi, (s.start_year, s.end_year),
                               label_visibility="collapsed")
        if (start, end) != (s.start_year, s.end_year):
            s.start_year, s.end_year = start, end
            s.year = end
            bump_map_nonce()
        return start, end
    return lo, hi
