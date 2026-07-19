"""Ticket list rendering shared by the Atlas, Shows page, drawers, profiles."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.filters import bill_for
from src.ui import ticket_html


def render_ticket_list(
    events: pd.DataFrame,
    artist_events: pd.DataFrame,
    limit: int = 50,
    newest_first: bool = True,
    variant: str | None = None,
    meta_map: dict[int, str] | None = None,
) -> None:
    """Render events as tickets. When variant is None, upcoming events get
    complete tickets and past events get torn stubs. meta_map optionally adds
    a data-derived line (e.g. "TIME #12") per event id."""
    ordered = events.sort_values(["event_date", "event_id"], ascending=not newest_first)
    shown = ordered.head(limit)
    html = "".join(
        ticket_html(
            row,
            bill_for(artist_events, row.event_id),
            variant or ("upcoming_full" if getattr(row, "is_upcoming", 0) else "past_torn"),
            meta=(meta_map or {}).get(int(row.event_id), ""),
        )
        for row in shown.itertuples()
    )
    st.markdown(html, unsafe_allow_html=True)
    remaining = len(ordered) - len(shown)
    if remaining > 0:
        st.caption(f"… and {remaining:,} more in this filter.")


def render_archive_sections(
    filtered: pd.DataFrame,
    artist_events: pd.DataFrame,
    ahead_label: str = "Still Ahead",
    archive_label: str = "From the Archive",
    limit: int = 8,
) -> None:
    """STILL AHEAD (complete tickets, soonest first) then FROM THE ARCHIVE
    (torn stubs, most recent first). Empty sections are omitted entirely."""
    ahead = filtered[filtered.is_upcoming == 1]
    past = filtered[filtered.is_upcoming == 0]
    if len(ahead):
        st.markdown(f'<div class="eyebrow">{ahead_label}</div>', unsafe_allow_html=True)
        render_ticket_list(ahead, artist_events, limit=limit, newest_first=False,
                           variant="upcoming_full")
    if len(past):
        st.markdown(f'<div class="eyebrow" style="margin-top:1rem">{archive_label}</div>',
                    unsafe_allow_html=True)
        render_ticket_list(past, artist_events, limit=limit, newest_first=True,
                           variant="past_torn")
