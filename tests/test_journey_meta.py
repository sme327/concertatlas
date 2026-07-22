from datetime import date
from pathlib import Path

import pandas as pd

from src.journey_meta import (
    home_for_date,
    infer_travel_mode,
    infer_venue_category,
    load_attendance_types,
    load_home_residences,
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


def test_load_home_residences_missing_file_returns_empty(tmp_path: Path):
    df = load_home_residences(tmp_path / "missing.csv")
    assert df.empty


def test_load_home_residences_open_start_and_sorting(tmp_path: Path):
    p = tmp_path / "homes.csv"
    p.write_text(
        "start_date,city,state_region,note\n"
        "2020-07-01,Seattle,Washington,later\n"
        ",Chicago,Illinois,first (open start)\n"
        "2013-03-01,San Jose,California,middle\n"
    )
    df = load_home_residences(p)
    assert list(df.city) == ["Chicago", "San Jose", "Seattle"]  # sorted, blank start first
    assert pd.isna(df.iloc[0].start_date)


def test_home_for_date_picks_effective_residence(tmp_path: Path):
    p = tmp_path / "homes.csv"
    p.write_text(
        "start_date,city,state_region\n"
        ",Chicago,Illinois\n"
        "2013-03-01,San Jose,California\n"
        "2020-07-01,Seattle,Washington\n"
    )
    df = load_home_residences(p)
    assert home_for_date("1999-01-01", df) == {"city": "Chicago", "state_region": "Illinois"}
    assert home_for_date("2013-02-28", df) == {"city": "Chicago", "state_region": "Illinois"}
    assert home_for_date("2013-03-01", df) == {"city": "San Jose", "state_region": "California"}
    assert home_for_date("2019-12-31", df) == {"city": "San Jose", "state_region": "California"}
    assert home_for_date("2020-07-01", df) == {"city": "Seattle", "state_region": "Washington"}
    assert home_for_date("2026-01-01", df) == {"city": "Seattle", "state_region": "Washington"}


def test_home_for_date_no_residences_configured():
    assert home_for_date("2020-01-01", load_home_residences(Path("/nonexistent"))) is None
