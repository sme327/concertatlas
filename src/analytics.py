from __future__ import annotations

from datetime import date

import pandas as pd


def filter_events(events: pd.DataFrame, start_year: int | None = None, end_year: int | None = None, artist_event_ids: set[int] | None = None) -> pd.DataFrame:
    out = events.copy()
    if start_year is not None:
        out = out[out.event_date.dt.year >= start_year]
    if end_year is not None:
        out = out[out.event_date.dt.year <= end_year]
    if artist_event_ids is not None:
        out = out[out.event_id.isin(artist_event_ids)]
    return out


def artist_summary(artist_events: pd.DataFrame) -> pd.DataFrame:
    return (artist_events.groupby(['artist_id', 'display_name'])
            .agg(appearances=('event_id', 'nunique'), first_seen=('event_date', 'min'), latest_seen=('event_date', 'max'), cities=('city_id', 'nunique'), venues=('venue_id', 'nunique'))
            .reset_index().sort_values(['appearances', 'display_name'], ascending=[False, True]))


def longest_gap_days(df: pd.DataFrame) -> int:
    dates = sorted(pd.to_datetime(df.event_date.dropna().unique()))
    if len(dates) < 2:
        return 0
    return max((b - a).days for a, b in zip(dates, dates[1:]))


def longest_gap_return(df: pd.DataFrame) -> pd.Series | None:
    """The event that ended the longest gap between appearances."""
    d = df.dropna(subset=['event_date']).sort_values('event_date')
    if len(d) < 2:
        return None
    gaps = d.event_date.diff()
    return d.loc[gaps.idxmax()]


def consecutive_year_streak(df: pd.DataFrame) -> int:
    years = sorted(set(pd.to_datetime(df.event_date.dropna()).dt.year))
    if not years:
        return 0
    best = cur = 1
    for a, b in zip(years, years[1:]):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


def coappearances(all_artist_events: pd.DataFrame, artist_id: int) -> pd.DataFrame:
    ids = set(all_artist_events.loc[all_artist_events.artist_id == artist_id, 'event_id'])
    return (all_artist_events[(all_artist_events.event_id.isin(ids)) & (all_artist_events.artist_id != artist_id)]
            .groupby(['artist_id', 'display_name']).event_id.nunique().reset_index(name='shared_bills')
            .sort_values(['shared_bills', 'display_name'], ascending=[False, True]))


def mark_upcoming(events: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """Recompute is_upcoming from the current date so the flag never goes stale."""
    today = today or date.today()
    out = events.copy()
    out['is_upcoming'] = (out.event_date.dt.date > today).fillna(False).astype(int)
    return out


def city_aggregates(filtered: pd.DataFrame, artist_events: pd.DataFrame) -> pd.DataFrame:
    """One row per city in the filtered event set, with map coordinates.

    Cities without resolved coordinates are kept (latitude/longitude NaN) so
    callers can both plot the resolved ones and report the unresolved ones.
    """
    if filtered.empty:
        return pd.DataFrame(columns=['city_id', 'city', 'state_region', 'latitude', 'longitude',
                                     'shows', 'venues', 'artists', 'first_date', 'latest_date'])
    ae = artist_events[artist_events.event_id.isin(filtered.event_id)]
    artists_per_city = ae.groupby('city_id').artist_id.nunique()
    agg = (filtered.groupby(['city_id', 'city', 'state_region'], dropna=False)
           .agg(latitude=('city_latitude', 'first'), longitude=('city_longitude', 'first'),
                shows=('event_id', 'nunique'), venues=('venue_id', 'nunique'),
                first_date=('event_date', 'min'), latest_date=('event_date', 'max'))
           .reset_index())
    agg['artists'] = agg.city_id.map(artists_per_city).fillna(0).astype(int)
    return agg.sort_values('shows', ascending=False)


def venue_aggregates(filtered: pd.DataFrame, artist_events: pd.DataFrame, city_id: int | None = None) -> pd.DataFrame:
    """One row per venue in the filtered event set (optionally one city only)."""
    subset = filtered if city_id is None else filtered[filtered.city_id == city_id]
    if subset.empty:
        return pd.DataFrame(columns=['venue_id', 'venue', 'city', 'state_region', 'latitude', 'longitude',
                                     'shows', 'artists', 'years', 'first_date', 'latest_date'])
    ae = artist_events[artist_events.event_id.isin(subset.event_id)]
    artists_per_venue = ae.groupby('venue_id').artist_id.nunique()
    agg = (subset.assign(year=subset.event_date.dt.year)
           .groupby(['venue_id', 'venue', 'city', 'state_region'], dropna=False)
           .agg(latitude=('venue_latitude', 'first'), longitude=('venue_longitude', 'first'),
                shows=('event_id', 'nunique'), years=('year', 'nunique'),
                first_date=('event_date', 'min'), latest_date=('event_date', 'max'))
           .reset_index())
    agg['artists'] = agg.venue_id.map(artists_per_venue).fillna(0).astype(int)
    return agg.sort_values('shows', ascending=False)


def venue_artist_constellation(filtered: pd.DataFrame, artist_events: pd.DataFrame, venue_id: int) -> pd.DataFrame:
    """Artists seen at a venue within the filtered window, with their years."""
    event_ids = set(filtered.loc[filtered.venue_id == venue_id, 'event_id'])
    ae = artist_events[artist_events.event_id.isin(event_ids)].copy()
    if ae.empty:
        return pd.DataFrame(columns=['artist_id', 'display_name', 'appearances', 'first_year', 'latest_year', 'years'])
    ae['year'] = ae.event_date.dt.year
    agg = (ae.groupby(['artist_id', 'display_name'])
           .agg(appearances=('event_id', 'nunique'), first_year=('year', 'min'),
                latest_year=('year', 'max'), years=('year', lambda y: sorted(set(y))))
           .reset_index()
           .sort_values(['appearances', 'display_name'], ascending=[False, True]))
    return agg


def year_counts(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=['event_date'])
    return d.groupby(d.event_date.dt.year).event_id.nunique().rename_axis('year').reset_index(name='shows')


def decade_counts(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=['event_date'])
    decade = (d.event_date.dt.year // 10) * 10
    return d.groupby(decade).event_id.nunique().rename_axis('decade').reset_index(name='shows')


def journey_sequence(filtered: pd.DataFrame, artist_events: pd.DataFrame) -> list[dict]:
    """Ordered journey stops for playback.

    Ordering: event_date then event_id (deterministic for same-date events).

    Coordinates: national/world-scale playback always uses the trusted
    canonical CITY coordinates (city_latitude/city_longitude) — never venue
    coordinates, which are reserved for a future reviewed city-level mode.
    Every event stays in the chronology, including those without resolved
    coordinates (has_coords False — retained in the detail card, never given
    a fabricated map point). draw_segment_from_prev is True only when this
    stop and the previous *resolved* stop have different coordinates, so
    repeat visits pulse in place instead of drawing loops. The route is the
    user's attendance order, not any performer's tour.
    """
    d = (filtered.dropna(subset=["event_date"])
         .sort_values(["event_date", "event_id"])
         .reset_index(drop=True))
    stops: list[dict] = []
    venue_visits: dict = {}
    city_visits: dict = {}
    region_visits: dict = {}
    prev_coords: tuple | None = None
    prev_date = None
    for i, row in enumerate(d.itertuples()):
        lat, lon = row.city_latitude, row.city_longitude
        has_coords = pd.notna(lat) and pd.notna(lon)
        coords = (round(float(lat), 6), round(float(lon), 6)) if has_coords else None
        venue_key = int(row.venue_id) if pd.notna(row.venue_id) else f"noven-{row.event_id}"
        city_key = int(row.city_id) if pd.notna(row.city_id) else f"nocity-{row.event_id}"
        region_key = str(row.state_region) if pd.notna(row.state_region) else f"noreg-{row.event_id}"
        venue_visits[venue_key] = venue_visits.get(venue_key, 0) + 1
        city_visits[city_key] = city_visits.get(city_key, 0) + 1
        region_visits[region_key] = region_visits.get(region_key, 0) + 1
        draw = bool(has_coords and prev_coords is not None and coords != prev_coords)
        bill_rows = artist_events[artist_events.event_id == row.event_id].sort_values("billing_order")
        stops.append(dict(
            event_id=int(row.event_id),
            event_date=str(pd.Timestamp(row.event_date).date()),
            event_title=str(row.event_title),
            venue_name=str(row.venue) if pd.notna(row.venue) else "",
            city_name=str(row.city) if pd.notna(row.city) else "",
            state_region=str(row.state_region) if pd.notna(row.state_region) else "",
            latitude=float(lat) if has_coords else None,
            longitude=float(lon) if has_coords else None,
            appearance_number=i + 1,
            location_visit_number=venue_visits[venue_key],
            city_visit_number=city_visits[city_key],
            region_visit_number=region_visits[region_key],
            is_upcoming=int(row.is_upcoming),
            has_coords=has_coords,
            draw_segment_from_prev=draw,
            days_since_prev=int((row.event_date - prev_date).days) if prev_date is not None else None,
            bill=bill_rows.display_name.tolist(),
        ))
        if has_coords:
            prev_coords = coords
        prev_date = row.event_date
    return stops


def region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Rooms-and-eras style summary grouped by recorded state/region."""
    d = df.dropna(subset=['event_date'])
    if d.empty:
        return pd.DataFrame(columns=['state_region', 'first_year', 'latest_year', 'appearances'])
    return (d.groupby('state_region', dropna=False)
            .agg(first_year=('event_date', lambda x: int(x.min().year)),
                 latest_year=('event_date', lambda x: int(x.max().year)),
                 appearances=('event_id', 'nunique'))
            .reset_index()
            .sort_values(['appearances', 'state_region'], ascending=[False, True]))
