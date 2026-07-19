from datetime import date
from pathlib import Path

from src.journey_meta import (
    infer_travel_mode,
    infer_venue_category,
    load_attendance_types,
    season_for,
)


def test_season_inference():
    assert season_for(date(2026, 1, 15)) == "winter"
    assert season_for(date(2026, 12, 5)) == "winter"
    assert season_for(date(2026, 4, 10)) == "spring"
    assert season_for(date(2026, 7, 4)) == "summer"
    assert season_for(date(2026, 10, 31)) == "fall"


def test_travel_mode_inference():
    assert infer_travel_mode(None) is None            # no movement
    assert infer_travel_mode(0.01) is None
    assert infer_travel_mode(1.2) == "walking"
    assert infer_travel_mode(90.0) == "car"
    assert infer_travel_mode(1700.0) == "airplane"
    assert infer_travel_mode(500.0, is_cruise=True) == "ship"


def test_venue_category_inference():
    assert infer_venue_category("First Midwest Bank Amphitheatre") == "amphitheater"
    assert infer_venue_category("Wrigley Field") == "stadium"
    assert infer_venue_category("Riviera Theatre") == "theater"
    assert infer_venue_category("Metro") == "club"
    assert infer_venue_category(None) == "club"


def test_attendance_loader(tmp_path: Path):
    assert load_attendance_types(tmp_path / "missing.csv") == {}
    p = tmp_path / "a.csv"
    p.write_text("event_id,attendance_type\n1,solo\n2,FRIENDS\n3,concert-buddies\n")
    out = load_attendance_types(p)
    assert out == {1: "solo", 2: "friends"}  # unknown values ignored, never guessed
