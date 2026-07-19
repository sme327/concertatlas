"""Event filtering. Every view derives its numbers from one filtered frame."""
from __future__ import annotations

import pandas as pd


def filter_events(
    events: pd.DataFrame,
    artist_events: pd.DataFrame | None = None,
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    artist_id: int | None = None,
    city_id: int | None = None,
    venue_id: int | None = None,
) -> pd.DataFrame:
    """Return the events matching the active time / artist / place selection."""
    out = events
    if start_year is not None:
        out = out[out.event_date.dt.year >= start_year]
    if end_year is not None:
        out = out[out.event_date.dt.year <= end_year]
    if artist_id is not None:
        if artist_events is None:
            raise ValueError("artist_events is required to filter by artist")
        ids = set(artist_events.loc[artist_events.artist_id == artist_id, "event_id"])
        out = out[out.event_id.isin(ids)]
    if city_id is not None:
        out = out[out.city_id == city_id]
    if venue_id is not None:
        out = out[out.venue_id == venue_id]
    return out.copy()


def bill_for(artist_events: pd.DataFrame, event_id: int) -> list[str]:
    """Ordered listed bill for one event, exactly as recorded."""
    rows = artist_events[artist_events.event_id == event_id].sort_values("billing_order")
    return rows.display_name.tolist()
