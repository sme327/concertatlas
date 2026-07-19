"""Geocode cities and venues into a local cache.

Requires network access and geopy. Results are cached in data/geocoded_locations.csv.
Failed or ambiguous lookups are written to data/geocode_review.csv for manual review;
corrections belong in data/geocode_manual_overrides.csv. Nothing is ever invented.

Usage: python scripts/geocode_locations.py
"""
from __future__ import annotations

import re
import ssl
import time
from pathlib import Path

import certifi
import pandas as pd
from geopy.geocoders import Nominatim

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
cache_path = DATA / "geocoded_locations.csv"
review_path = DATA / "geocode_review.csv"

US_STATES = {
    "Arizona", "California", "Colorado", "Florida", "Georgia", "Illinois",
    "Indiana", "Iowa", "Kentucky", "Maryland", "Michigan", "Minnesota",
    "Missouri", "Montana", "Nevada", "New Jersey", "Ohio", "Oregon",
    "Pennsylvania", "Tennessee", "Texas", "Utah", "Virginia", "Washington",
    "Wisconsin",
}
COUNTRY_REGIONS = {"Canada": "Canada", "England": "United Kingdom"}
UNPLOTTABLE_REGIONS = {"Atlantic Ocean"}


def split_region(state_region: str) -> tuple[str, str]:
    """Split a recorded state_region into (region, country) for query building.

    Handles 'Alberta (Canada)' style values, bare countries, and US states.
    Returns ('', '') for values with no fixed location (e.g. 'Atlantic Ocean').
    """
    s = (state_region or "").strip()
    if not s or s in UNPLOTTABLE_REGIONS:
        return "", ""
    m = re.match(r"^(.*?)\s*\((.+)\)$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if s in COUNTRY_REGIONS:
        return "", COUNTRY_REGIONS[s]
    if s in US_STATES:
        return s, "USA"
    return s, ""


def load_cache() -> tuple[pd.DataFrame, set[str]]:
    if cache_path.exists():
        cache = pd.read_csv(cache_path)
        if len(cache):
            keys = set(
                cache[["location_type", "venue", "city", "state_region"]]
                .fillna("")
                .astype(str)
                .agg("|".join, axis=1)
            )
            return cache, keys
    return pd.DataFrame(), set()


def main() -> None:
    cache, existing = load_cache()
    rows: list[dict] = []
    reviews: list[dict] = []
    # macOS system Python has no CA bundle wired up; use certifi's.
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    geolocator = Nominatim(user_agent="the-long-encore-local-geocoder", ssl_context=ssl_context)

    def clean(value) -> str:
        s = str(value or "")
        return "" if s == "nan" else s.strip()

    def run(kind: str, frame: pd.DataFrame) -> None:
        for _, r in frame.iterrows():
            venue = "" if kind == "city" else clean(r.get("venue_name_recorded", ""))
            city = clean(r.get("city", ""))
            state_region = clean(r.get("state_region", ""))
            key = "|".join([kind, venue, city, state_region])
            if key in existing:
                continue
            region, country = split_region(state_region)
            if not region and not country and state_region:
                reviews.append(dict(
                    location_type=kind, venue=venue, city=city,
                    state_region=state_region, country="", query="",
                    status="unplottable_region", candidate="",
                    review_note=f"Region '{state_region}' has no fixed coordinates; add a manual override if desired.",
                ))
                continue
            query = ", ".join(x for x in [venue, city, region, country] if x)
            try:
                loc = geolocator.geocode(query, exactly_one=True, timeout=15)
                if loc:
                    rows.append(dict(
                        location_type=kind, canonical_name=venue or city,
                        venue=venue, city=city, state_region=state_region,
                        country=country, latitude=loc.latitude,
                        longitude=loc.longitude, geocode_status="resolved",
                        source="Nominatim", review_note="",
                    ))
                else:
                    reviews.append(dict(
                        location_type=kind, venue=venue, city=city,
                        state_region=state_region, country=country, query=query,
                        status="not_found", candidate="", review_note="Review manually.",
                    ))
            except Exception as exc:
                reviews.append(dict(
                    location_type=kind, venue=venue, city=city,
                    state_region=state_region, country=country, query=query,
                    status="error", candidate="", review_note=str(exc),
                ))
            time.sleep(1.1)

    run("city", pd.read_csv(DATA / "cities_to_geocode.csv"))
    run("venue", pd.read_csv(DATA / "venues_to_geocode.csv"))
    if rows:
        pd.concat([cache, pd.DataFrame(rows)], ignore_index=True).to_csv(cache_path, index=False)
    if reviews:
        pd.DataFrame(reviews).to_csv(review_path, index=False)
    print(f"Added {len(rows)} resolved locations; {len(reviews)} need review.")


if __name__ == "__main__":
    main()
