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
