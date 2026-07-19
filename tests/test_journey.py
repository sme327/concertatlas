import pandas as pd

from src.analytics import journey_sequence
from tests.test_analytics import make_artist_events, make_events


def seq(events=None, ae=None):
    return journey_sequence(events if events is not None else make_events(),
                            ae if ae is not None else make_artist_events())


def test_strict_date_order_with_event_id_tiebreak():
    events = make_events()
    # Give two events the same date; event_id must break the tie deterministically.
    events.loc[events.event_id == 3, "event_date"] = pd.Timestamp("2005-07-01")
    stops = seq(events)
    assert [s["event_id"] for s in stops] == [1, 2, 3, 4]


def test_all_same_date_events_preserved_not_collapsed():
    stops = seq()
    assert len(stops) == 4
    assert [s["appearance_number"] for s in stops] == [1, 2, 3, 4]


def test_same_coordinates_do_not_draw_segment():
    stops = seq()
    # Events 1 and 2 are both in Chicago at identical city coordinates.
    assert stops[0]["draw_segment_from_prev"] is False  # first stop ever
    assert stops[1]["draw_segment_from_prev"] is False  # same place as previous


def test_return_to_earlier_location_draws_new_segment():
    events = make_events()
    # Resolve Seattle, then send event 4 back to Chicago's coordinates.
    events.loc[events.city_id == 20, ["city_latitude", "city_longitude"]] = [47.6, -122.3]
    events.loc[events.event_id == 4, ["city_id", "city", "city_latitude", "city_longitude"]] = \
        [10, "Chicago", 41.9, -87.6]
    stops = seq(events)
    assert stops[2]["draw_segment_from_prev"] is True   # Chicago -> Seattle
    assert stops[3]["draw_segment_from_prev"] is True   # Seattle -> back to Chicago


def test_unresolved_coordinates_stay_in_chronology_without_map_point():
    stops = seq()  # Seattle city rows have NaN coordinates in the fixture
    seattle = [s for s in stops if s["city_name"] == "Seattle"]
    assert len(seattle) == 2
    assert all(s["has_coords"] is False and s["latitude"] is None for s in seattle)
    assert all(s["draw_segment_from_prev"] is False for s in seattle)


def test_segment_resumes_from_last_resolved_location():
    events = make_events()
    # Chicago (resolved) -> Seattle (unresolved) -> Portland (resolved):
    events.loc[events.event_id == 4, ["city_id", "city", "city_latitude", "city_longitude"]] = \
        [30, "Portland", 45.5, -122.6]
    stops = seq(events)
    assert stops[3]["draw_segment_from_prev"] is True  # drawn from Chicago, skipping unresolved Seattle


def test_visit_counters_accumulate():
    stops = seq()
    assert [s["city_visit_number"] for s in stops] == [1, 2, 1, 2]
    # Venue 200 hosts events 3 and 4; venues 100/101 once each.
    assert [s["location_visit_number"] for s in stops] == [1, 1, 1, 2]


def test_bill_preserved_in_stop():
    stops = seq()
    assert stops[0]["bill"] == ["Counting Crows", "Live"]


def test_upcoming_flag_passes_through():
    assert [s["is_upcoming"] for s in seq()] == [0, 0, 0, 1]


def test_region_visit_numbers_accumulate():
    stops = seq()  # Illinois, Illinois, Washington, Washington
    assert [s["region_visit_number"] for s in stops] == [1, 2, 1, 2]


def test_days_since_prev():
    stops = seq()  # 1999-06-01, 2005-07-01, 2005-09-01, 2026-12-01
    assert stops[0]["days_since_prev"] is None
    assert stops[2]["days_since_prev"] == 62
    assert stops[3]["days_since_prev"] > 365 * 20


def test_cinematic_metadata_fields():
    stops = seq()
    assert stops[0]["travel_mode"] is None and stops[0]["travel_miles"] is None  # first stop
    assert stops[1]["travel_mode"] is None      # same Chicago coordinates: no movement
    assert [s["season"] for s in stops] == ["summer", "summer", "fall", "winter"]
    assert stops[0]["venue_category"] == "club"  # Metro


def test_venue_coords_only_when_validated():
    events = make_events()
    stops = journey_sequence(events, make_artist_events())
    # Chicago venues sit ~1-2 miles from the city point -> validated for street view.
    assert stops[0]["venue_latitude"] is not None
    # A venue far from its city must be withheld from the street camera.
    events.loc[events.event_id == 1, ["venue_latitude", "venue_longitude"]] = [45.0, -93.0]
    stops2 = journey_sequence(events, make_artist_events())
    assert stops2[0]["venue_latitude"] is None
    # Unresolved city -> no venue coordinate either (city trust comes first).
    seattle = [s for s in stops if s["city_name"] == "Seattle"]
    assert all(s["venue_latitude"] is None for s in seattle)


def test_attendance_types_attached_only_when_supplied():
    stops = journey_sequence(make_events(), make_artist_events(), attendance_types={1: "friends"})
    assert stops[0]["attendance_type"] == "friends"
    assert stops[1]["attendance_type"] is None
