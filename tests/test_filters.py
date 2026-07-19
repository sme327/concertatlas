import pandas as pd

from src.filters import bill_for, filter_events
from tests.test_analytics import make_artist_events, make_events


def test_artist_plus_time_filter():
    out = filter_events(make_events(), make_artist_events(),
                        start_year=2005, end_year=2010, artist_id=7)
    assert out.event_id.tolist() == [2, 3]


def test_place_filters():
    events, ae = make_events(), make_artist_events()
    assert filter_events(events, city_id=10).event_id.tolist() == [1, 2]
    assert filter_events(events, venue_id=200).event_id.tolist() == [3, 4]


def test_bill_preserves_recorded_order():
    assert bill_for(make_artist_events(), 1) == ["Counting Crows", "Live"]
