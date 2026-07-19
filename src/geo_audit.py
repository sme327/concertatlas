"""Geographic validation: a non-null coordinate is not automatically a valid one.

Every venue coordinate is compared against its parent city's canonical
coordinate; anything beyond the allowed distance is flagged for review rather
than trusted. The journey uses city coordinates at national scale, so venue
coordinates only matter for a future (reviewed) city-level mode.
"""
from __future__ import annotations

import math

import pandas as pd

VENUE_CITY_FLAG_MILES = 50.0     # beyond this the venue coordinate is untrusted
VENUE_CITY_REVIEW_MILES = 6.0    # metro-plausible but worth a look


def distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (lat1, lon1, lat2, lon2))
    return 3959.0 * math.acos(min(1.0, math.sin(la1) * math.sin(la2)
                                  + math.cos(la1) * math.cos(la2) * math.cos(lo1 - lo2)))


def classify_venue_distance(miles: float | None) -> str:
    if miles is None:
        return "unresolved"
    if miles > VENUE_CITY_FLAG_MILES:
        return "FLAG_gt_50mi"
    if miles > VENUE_CITY_REVIEW_MILES:
        return "review_gt_6mi"
    return "ok"


def venue_coordinate_audit(venues: pd.DataFrame) -> pd.DataFrame:
    """Audit rows need: venue_id, venue_name_recorded, city, state_region,
    latitude/longitude (venue) and city_lat/city_lon (parent city)."""
    rows = []
    for r in venues.itertuples():
        if pd.isna(r.latitude) or pd.isna(getattr(r, "city_lat")):
            miles, status = None, ("venue_unresolved" if pd.isna(r.latitude) else "city_unresolved")
        else:
            miles = distance_miles(r.latitude, r.longitude, r.city_lat, r.city_lon)
            status = classify_venue_distance(miles)
        rows.append(dict(
            venue_id=r.venue_id, venue=r.venue_name_recorded, city=r.city,
            state_region=r.state_region, venue_lat=r.latitude, venue_lon=r.longitude,
            city_lat=r.city_lat, city_lon=r.city_lon,
            venue_city_miles=round(miles, 1) if miles is not None else None,
            status=status,
        ))
    return pd.DataFrame(rows)
