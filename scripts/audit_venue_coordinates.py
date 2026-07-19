"""Write the venue-coordinate audit for later cleanup.

Compares every venue coordinate to its parent city's canonical coordinate and
writes data/venue_coordinate_audit.csv. Venues flagged here should not be
trusted for any future city-level journey mode until reviewed (corrections go
in data/geocode_manual_overrides.csv).

Usage: python scripts/audit_venue_coordinates.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.geo_audit import venue_coordinate_audit  # noqa: E402


def main() -> None:
    con = sqlite3.connect(ROOT / "data" / "concerts.sqlite")
    venues = pd.read_sql_query(
        """SELECT v.venue_id, v.venue_name_recorded, v.latitude, v.longitude,
                  c.city, c.state_region, c.latitude AS city_lat, c.longitude AS city_lon
           FROM venues v LEFT JOIN cities c ON c.city_id = v.city_id""", con)
    con.close()
    audit = venue_coordinate_audit(venues)
    out = ROOT / "data" / "venue_coordinate_audit.csv"
    audit.to_csv(out, index=False)
    print(f"Wrote {out}")
    print(audit.status.value_counts().to_string())
    flagged = audit[audit.status.str.startswith(("FLAG", "review"))]
    if len(flagged):
        print("\nNeeds review:")
        print(flagged[["venue", "city", "state_region", "venue_city_miles", "status"]]
              .to_string(index=False))


if __name__ == "__main__":
    main()
