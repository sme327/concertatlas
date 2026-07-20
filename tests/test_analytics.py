from datetime import date

import pandas as pd

from src.analytics import (
    city_aggregates,
    coappearances,
    consecutive_year_streak,
    decade_counts,
    filter_events,
    longest_gap_days,
    longest_gap_return,
    mark_upcoming,
    region_summary,
    venue_aggregates,
    venue_artist_constellation,
    year_counts,
)


def make_events():
    return pd.DataFrame({
        "event_id": [1, 2, 3, 4],
        "event_date": pd.to_datetime(["1999-06-01", "2005-07-01", "2005-09-01", "2026-12-01"]),
        "event_title": ["A", "B", "C", "D"],
        "city_id": [10, 10, 20, 20],
        "city": ["Chicago", "Chicago", "Seattle", "Seattle"],
        "state_region": ["Illinois", "Illinois", "Washington", "Washington"],
        "venue_id": [100, 101, 200, 200],
        "venue": ["Metro", "Vic", "Showbox", "Showbox"],
        "city_latitude": [41.9, 41.9, None, None],
        "city_longitude": [-87.6, -87.6, None, None],
        "venue_latitude": [41.95, 41.94, None, None],
        "venue_longitude": [-87.65, -87.64, None, None],
        "is_upcoming": [0, 0, 0, 1],
    })


def make_artist_events():
    return pd.DataFrame({
        "event_id": [1, 1, 2, 3, 4],
        "artist_id": [7, 8, 7, 7, 9],
        "display_name": ["Counting Crows", "Live", "Counting Crows", "Counting Crows", "Foo"],
        "billing_order": [0, 1, 0, 0, 0],
        "event_date": pd.to_datetime(["1999-06-01", "1999-06-01", "2005-07-01", "2005-09-01", "2026-12-01"]),
        "city_id": [10, 10, 10, 20, 20],
        "venue_id": [100, 100, 101, 200, 200],
    })


def test_filter_year_range():
    df = pd.DataFrame({'event_id': [1, 2, 3],
                       'event_date': pd.to_datetime(['1999-01-01', '2005-01-01', '2010-01-01'])})
    assert filter_events(df, 2000, 2009).event_id.tolist() == [2]


def test_single_year_filter():
    events = make_events()
    out = filter_events(events, 2005, 2005)
    assert out.event_id.tolist() == [2, 3]


def test_longest_gap():
    df = pd.DataFrame({'event_date': pd.to_datetime(['2000-01-01', '2001-01-01', '2004-01-01'])})
    assert longest_gap_days(df) == 1095


def test_longest_gap_return_is_event_after_gap():
    df = pd.DataFrame({'event_id': [1, 2, 3],
                       'event_date': pd.to_datetime(['2000-01-01', '2001-01-01', '2004-01-01'])})
    assert longest_gap_return(df).event_id == 3


def test_streak():
    df = pd.DataFrame({'event_date': pd.to_datetime(['2000-01-01', '2001-02-01', '2002-03-01', '2005-01-01'])})
    assert consecutive_year_streak(df) == 3


def test_coappearance_counts():
    co = coappearances(make_artist_events(), 7)
    assert co.loc[co.display_name == "Live", "shared_bills"].iloc[0] == 1
    assert "Counting Crows" not in co.display_name.tolist()


def test_mark_upcoming():
    out = mark_upcoming(make_events(), today=date(2026, 7, 17))
    assert out.is_upcoming.tolist() == [0, 0, 0, 1]
    out2 = mark_upcoming(make_events(), today=date(2027, 1, 1))
    assert out2.is_upcoming.sum() == 0


def test_city_aggregates_counts_and_unresolved_kept():
    agg = city_aggregates(make_events(), make_artist_events())
    chicago = agg[agg.city_id == 10].iloc[0]
    assert chicago.shows == 2 and chicago.venues == 2 and chicago.artists == 2
    seattle = agg[agg.city_id == 20].iloc[0]
    assert pd.isna(seattle.latitude)  # unresolved coordinates preserved, never invented
    assert len(agg) == 2


def test_venue_aggregates_scoped_to_city():
    agg = venue_aggregates(make_events(), make_artist_events(), city_id=20)
    assert agg.venue_id.tolist() == [200]
    assert agg.iloc[0].shows == 2


def test_venue_constellation_years():
    con = venue_artist_constellation(make_events(), make_artist_events(), 200)
    crows = con[con.artist_id == 7].iloc[0]
    assert crows.appearances == 1 and crows.years == [2005]


def test_year_and_decade_counts():
    yc = year_counts(make_events())
    assert yc.set_index("year").loc[2005, "shows"] == 2
    dc = decade_counts(make_events())
    assert dc.set_index("decade").loc[2000, "shows"] == 2


def test_region_summary():
    reg = region_summary(make_events())
    il = reg[reg.state_region == "Illinois"].iloc[0]
    assert (il.first_year, il.latest_year, il.appearances) == (1999, 2005, 2)


def test_country_for_region():
    from src.analytics import country_for_region
    assert country_for_region("Illinois") == "USA"
    assert country_for_region("Alberta (Canada)") == "Canada"
    assert country_for_region("Canada") == "Canada"
    assert country_for_region("England") == "United Kingdom"
    assert country_for_region("Atlantic Ocean") is None
    assert country_for_region(None) is None


def test_geo_metrics():
    from src.analytics import geo_metrics
    gm = geo_metrics(make_events())  # Illinois + Washington
    assert gm == {"states": 2, "countries": 1}


def test_year_breakdown_top_artist_and_venue():
    from src.analytics import year_breakdown
    yb = year_breakdown(make_events(), make_artist_events()).set_index("year")
    assert yb.loc[2005, "shows"] == 2
    assert yb.loc[2005, "top_artist"] == "Counting Crows"
    assert yb.loc[1999, "top_venue"] == "Metro"
    assert bool(yb.loc[2026, "has_upcoming"]) is True
    assert bool(yb.loc[1999, "has_upcoming"]) is False
