from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics import mark_upcoming

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "concerts.sqlite"


def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def event_frame(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    query = """
    SELECT e.*, v.canonical_venue_name AS venue, c.city, c.state_region,
           c.latitude AS city_latitude, c.longitude AS city_longitude,
           v.latitude AS venue_latitude, v.longitude AS venue_longitude
    FROM events e
    LEFT JOIN venues v ON e.venue_id=v.venue_id
    LEFT JOIN cities c ON e.city_id=c.city_id
    """
    with connect(db_path) as conn:
        df = pd.read_sql_query(query, conn, parse_dates=["event_date"])
    return mark_upcoming(df)


def artist_frame(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    query = """
    SELECT ea.event_id, ea.artist_id, ea.billing_order, ea.is_event_title,
           a.display_name, e.event_date, e.event_title, e.venue_id, e.city_id,
           v.canonical_venue_name AS venue, c.city, c.state_region
    FROM event_artists ea
    JOIN artists a ON a.artist_id=ea.artist_id
    JOIN events e ON e.event_id=ea.event_id
    LEFT JOIN venues v ON v.venue_id=e.venue_id
    LEFT JOIN cities c ON c.city_id=e.city_id
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(query, conn, parse_dates=["event_date"])


def city_coordinates(db_path: Path = DEFAULT_DB) -> dict[tuple[str, str], tuple[float, float]]:
    """(city, state_region) -> (latitude, longitude) for every resolved city.

    The single source of truth for "where is this city" — home residences
    and anything else that needs a city point look it up here rather than
    carrying a second, potentially-inconsistent coordinate.
    """
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT city, state_region, latitude, longitude FROM cities WHERE latitude IS NOT NULL"
        ).fetchall()
    return {(r["city"], r["state_region"]): (r["latitude"], r["longitude"]) for r in rows}


def geocode_coverage(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Resolved vs unresolved coordinate counts for cities and venues."""
    query = """
    SELECT 'city' AS location_type,
           COALESCE(geocode_status, 'unresolved') AS status, COUNT(*) AS n
    FROM cities GROUP BY 1, 2
    UNION ALL
    SELECT 'venue', COALESCE(geocode_status, 'unresolved'), COUNT(*)
    FROM venues GROUP BY 1, 2
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(query, conn)


def unresolved_locations(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Locations that could not be plotted, for the About page."""
    query = """
    SELECT 'city' AS location_type, c.city AS name, c.state_region, COUNT(e.event_id) AS events
    FROM cities c LEFT JOIN events e ON e.city_id=c.city_id
    WHERE c.latitude IS NULL GROUP BY c.city_id
    UNION ALL
    SELECT 'venue', v.venue_name_recorded, c.state_region, COUNT(e.event_id)
    FROM venues v LEFT JOIN cities c ON c.city_id=v.city_id
                  LEFT JOIN events e ON e.venue_id=v.venue_id
    WHERE v.latitude IS NULL GROUP BY v.venue_id
    ORDER BY events DESC
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(query, conn)
