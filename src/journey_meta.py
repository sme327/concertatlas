"""Pure metadata inference for cinematic journey playback.

Everything here is presentation-layer inference derived from real data
(distances, dates, venue names) or from the optional user-maintained
attendance file. Nothing is asserted as fact anywhere in the UI.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

# Travel-mode thresholds (miles between consecutive city points).
WALKING_MAX_MILES = 2.0
DRIVE_MAX_MILES = 250.0

ATTENDANCE_TYPES = {"solo", "couple", "friends", "family", "festival"}

VENUE_CATEGORY_KEYWORDS = [
    ("amphitheater", ("amphitheat", "gorge", "pavilion", "shell", "meadows", "lawn")),
    ("stadium", ("stadium", "arena", "field", "coliseum", "dome", "garden")),
    ("theater", ("theatre", "theater", "opera", "hall", "auditorium", "playhouse")),
    ("festival_grounds", ("festival", "grounds", "fairground", "park")),
]


def season_for(d: date | pd.Timestamp) -> str:
    m = pd.Timestamp(d).month
    if m in (12, 1, 2):
        return "winter"
    if m in (3, 4, 5):
        return "spring"
    if m in (6, 7, 8):
        return "summer"
    return "fall"


def infer_travel_mode(miles: float | None, is_cruise: bool = False) -> str | None:
    """How this leg was probably traveled. None = no movement / unknown."""
    if is_cruise:
        return "ship"
    if miles is None or miles < 0.05:
        return None
    if miles < WALKING_MAX_MILES:
        return "walking"
    if miles < DRIVE_MAX_MILES:
        return "car"
    return "airplane"


def infer_venue_category(venue_name: str | None) -> str:
    """Coarse venue type from the recorded name — presentation only (drives
    camera framing), never displayed as a fact."""
    name = (venue_name or "").lower()
    for category, keywords in VENUE_CATEGORY_KEYWORDS:
        if any(k in name for k in keywords):
            return category
    return "club"


def load_home_residences(path: Path) -> pd.DataFrame:
    """Optional user-maintained home history: start_date,city,state_region[,note].

    Each residence is in effect from its start_date until the next row's
    start_date begins; the last row extends to today. A blank start_date on
    the first row means "since before the data began." Returns an empty
    frame (never a fabricated guess) if the file is missing or malformed —
    callers should treat that as "no home routing available."
    """
    empty = pd.DataFrame(columns=["start_date", "city", "state_region", "note"])
    if not path.exists():
        return empty
    try:
        df = pd.read_csv(path)
    except Exception:
        return empty
    if not len(df) or "city" not in df.columns or "state_region" not in df.columns:
        return empty
    df = df.dropna(subset=["city", "state_region"]).copy()
    df["start_date"] = pd.to_datetime(df.get("start_date"), errors="coerce")
    return df.sort_values("start_date", na_position="first").reset_index(drop=True)


def home_for_date(event_date, residences: pd.DataFrame) -> dict | None:
    """The residence in effect on event_date, or None if none are configured.

    The result carries only city/state_region — coordinates are resolved by
    the caller against the trusted cities table, the same way every other
    location in the app is, so home points are never a separate/uncertain
    coordinate source.
    """
    if residences.empty:
        return None
    ts = pd.Timestamp(event_date)
    eligible = residences[residences.start_date.isna() | (residences.start_date <= ts)]
    row = eligible.iloc[-1] if len(eligible) else residences.iloc[0]
    return {"city": row.city, "state_region": row.state_region}


def load_attendance_types(path: Path) -> dict[int, str]:
    """Optional user-maintained metadata: event_id,attendance_type.
    Unknown values are ignored rather than guessed."""
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}
    if "event_id" not in df.columns or "attendance_type" not in df.columns:
        return {}
    out: dict[int, str] = {}
    for r in df.itertuples():
        val = str(r.attendance_type).strip().lower()
        if val in ATTENDANCE_TYPES and pd.notna(r.event_id):
            out[int(r.event_id)] = val
    return out
