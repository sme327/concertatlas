"""Coordinate-policy tests: Journey trusts canonical city coordinates at
national scale; venue coordinates can never override them, and geographic
validation never equates non-null with valid."""
import json

import pandas as pd
import pytest

from src.analytics import journey_sequence
from src.geo_audit import classify_venue_distance, distance_miles, venue_coordinate_audit
from tests.test_analytics import make_artist_events, make_events


def test_journey_uses_city_coordinates_not_venue():
    events = make_events()
    # Give every event a venue coordinate far from its city; the journey must ignore it.
    events["venue_latitude"] = 10.0
    events["venue_longitude"] = 10.0
    stops = journey_sequence(events, make_artist_events())
    chicago = [s for s in stops if s["city_name"] == "Chicago"]
    assert all(s["latitude"] == 41.9 and s["longitude"] == -87.6 for s in chicago)


def test_venue_coordinates_cannot_override_trusted_city():
    events = make_events()
    # Seattle city coords are unresolved in the fixture, but its venue has coords:
    events.loc[events.city_id == 20, ["venue_latitude", "venue_longitude"]] = [47.6, -122.3]
    stops = journey_sequence(events, make_artist_events())
    seattle = [s for s in stops if s["city_name"] == "Seattle"]
    # No fallback to venue coords: unresolved city stays unmapped rather than guessed.
    assert all(s["has_coords"] is False and s["latitude"] is None for s in seattle)


def test_journey_payload_serializes_lon_lat_for_maplibre():
    stops = journey_sequence(make_events(), make_artist_events())
    payload = json.loads(json.dumps(stops))
    s = payload[0]
    # MapLibre consumes [longitude, latitude]; the player builds it from these fields.
    assert [s["longitude"], s["latitude"]] == [-87.6, 41.9]
    assert -90 <= s["latitude"] <= 90 and -180 <= s["longitude"] <= 180


def test_far_venue_flagged_for_review():
    assert classify_venue_distance(51.0) == "FLAG_gt_50mi"
    assert classify_venue_distance(10.0) == "review_gt_6mi"
    assert classify_venue_distance(2.0) == "ok"
    assert classify_venue_distance(None) == "unresolved"


def test_distance_miles_sanity():
    # Chicago -> Milwaukee is roughly 80-85 miles.
    d = distance_miles(41.8756, -87.6244, 43.0386, -87.9091)
    assert 75 < d < 95


def test_venue_audit_flags_and_never_trusts_nonnull():
    venues = pd.DataFrame([
        # venue right in town -> ok
        dict(venue_id=1, venue_name_recorded="Metro", city="Chicago", state_region="Illinois",
             latitude=41.95, longitude=-87.65, city_lat=41.8756, city_lon=-87.6244),
        # non-null but wildly wrong (southern hemisphere) -> flagged, not accepted
        dict(venue_id=2, venue_name_recorded="Bad Geo Hall", city="Chicago", state_region="Illinois",
             latitude=-33.9, longitude=-60.0, city_lat=41.8756, city_lon=-87.6244),
        # unresolved venue stays unresolved
        dict(venue_id=3, venue_name_recorded="Lost Room", city="Chicago", state_region="Illinois",
             latitude=None, longitude=None, city_lat=41.8756, city_lon=-87.6244),
    ])
    audit = venue_coordinate_audit(venues)
    by_id = audit.set_index("venue_id").status
    assert by_id[1] == "ok"
    assert by_id[2] == "FLAG_gt_50mi"
    assert by_id[3] == "venue_unresolved"
