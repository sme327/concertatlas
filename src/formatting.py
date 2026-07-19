"""Small presentation helpers shared across pages."""
from __future__ import annotations

import html

import pandas as pd


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def fmt_date(value) -> str:
    if value is None or pd.isna(value):
        return "—"
    return pd.Timestamp(value).strftime("%b %d, %Y")


def fmt_date_upper(value) -> str:
    return fmt_date(value).upper()


def year_of(value) -> str:
    if value is None or pd.isna(value):
        return "—"
    return str(pd.Timestamp(value).year)


def year_span(first, latest) -> str:
    a, b = year_of(first), year_of(latest)
    return a if a == b else f"{a}–{b}"


def plural(n: int, word: str, plural_word: str | None = None) -> str:
    return f"{n:,} {word if n == 1 else (plural_word or word + 's')}"


def place_line(city, state_region) -> str:
    parts = [str(p) for p in (city, state_region) if p is not None and not pd.isna(p) and str(p).strip()]
    return ", ".join(parts)


def artist_journey_sentence(name: str, events: pd.DataFrame) -> str:
    """A single sentence derived only from confirmed data."""
    d = events.dropna(subset=["event_date"]).sort_values("event_date")
    if d.empty:
        return ""
    first, latest = d.iloc[0], d.iloc[-1]
    years = latest.event_date.year - first.event_date.year
    n = d.event_id.nunique()
    if years <= 0:
        return (f"You have seen {name} {plural(n, 'time')}, "
                f"starting at {first.venue} in {place_line(first.city, first.state_region)} in {first.event_date.year}.")
    return (f"You have seen {name} {plural(n, 'time')} across {years} years — "
            f"from {place_line(first.city, first.state_region)} in {first.event_date.year} "
            f"to {place_line(latest.city, latest.state_region)} in {latest.event_date.year}.")
