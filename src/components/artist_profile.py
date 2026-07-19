"""Artist profile rendering: rich deep-dives for the top artists, a clean
functional profile for everyone else. All numbers derive from the events
passed in, which are already bounded by the active time filter.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    city_aggregates,
    coappearances,
    consecutive_year_streak,
    decade_counts,
    longest_gap_days,
    longest_gap_return,
    region_summary,
    venue_aggregates,
    year_counts,
)
from src.components.event_cards import render_ticket_list
from src.components.map_view import HOVER_STYLE, city_map
from src.config import AMBER, INK, MUTED
from src.filters import bill_for
from src.formatting import esc, fmt_date, place_line
from src.ui import bar_rows_html, ticket_html, year_strip_html

SHARED_BILLS_CAVEAT = "Based on names listed for the same event; billing roles are not inferred."


def _moment(label: str, row: pd.Series | None, artist_events: pd.DataFrame) -> None:
    """One relationship moment (First/Latest/Next Time) as a compact ticket."""
    if row is None:
        return
    st.markdown(f'<div class="eyebrow" style="margin-top:.6rem">{esc(label)}</div>', unsafe_allow_html=True)
    st.markdown(ticket_html(row, bill_for(artist_events, int(row.event_id)), "journey_compact"),
                unsafe_allow_html=True)


def _hero(name: str, filtered: pd.DataFrame, artist_events: pd.DataFrame) -> None:
    """An introduction to a relationship, not a KPI row."""
    d = filtered.dropna(subset=["event_date"]).sort_values(["event_date", "event_id"])
    n = d.event_id.nunique()
    years = 0
    if len(d):
        years = d.event_date.max().year - d.event_date.min().year
    span_phrase = f"{n} time{'s' if n != 1 else ''} seen" + (f" across {years} years" if years else "")
    places = d.city_id.nunique()
    venues = d.venue_id.nunique()
    st.markdown(
        f'<div class="eyebrow">Artist</div>'
        f'<div class="hero-title">{esc(name.upper())}</div>'
        f'<div class="muted">{span_phrase} · {places} place{"s" if places != 1 else ""} · '
        f'{venues} venue{"s" if venues != 1 else ""}</div>',
        unsafe_allow_html=True,
    )
    past = d[d.is_upcoming == 0]
    ahead = d[d.is_upcoming == 1]
    m1, m2, m3 = st.columns(3)
    with m1:
        _moment("First time", past.iloc[0] if len(past) else (d.iloc[0] if len(d) else None), artist_events)
    with m2:
        if len(past) > 1:
            _moment("Latest time", past.iloc[-1], artist_events)
    with m3:
        if len(ahead):
            _moment("Next time", ahead.iloc[0], artist_events)


def _timeline(artist_name: str, events: pd.DataFrame, artist_events: pd.DataFrame) -> None:
    """Every time seen as a dot: x = position in the year, y = year."""
    d = events.dropna(subset=["event_date"]).sort_values(["event_date", "event_id"]).reset_index(drop=True)
    if d.empty:
        return
    d["appearance_no"] = np.arange(1, len(d) + 1)
    day = d.event_date.dt.dayofyear
    years = d.event_date.dt.year
    customdata = np.stack([
        d.event_id.astype(int),
        d.event_date.map(fmt_date),
        d.venue.astype(str),
        d.city.astype(str) + ", " + d.state_region.astype(str),
        d.appearance_no.astype(int),
    ], axis=-1)
    fig = go.Figure(go.Scatter(
        x=day, y=years, mode="markers",
        marker=dict(size=10, color=AMBER, opacity=0.85),
        customdata=customdata,
        hovertemplate=("<b>Time #%{customdata[4]}</b><br>%{customdata[1]}<br>"
                       "%{customdata[2]} · %{customdata[3]}<extra></extra>"),
    ))
    fig.update_layout(
        height=max(240, 26 * years.nunique() + 80),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=INK, plot_bgcolor=INK,
        xaxis=dict(title="", tickvals=[1, 91, 182, 274, 350],
                   ticktext=["JAN", "APR", "JUL", "OCT", "DEC"],
                   gridcolor="#1a2124", color=MUTED, range=[-5, 372]),
        yaxis=dict(title="", autorange="reversed", gridcolor="#1a2124",
                   color=MUTED, dtick=1, tickformat="d"),
        hoverlabel=HOVER_STYLE,
        showlegend=False,
    )
    event = st.plotly_chart(fig, width="stretch", on_select="rerun",
                            selection_mode=("points",), key=f"timeline_{artist_name}")
    points = event.selection.points if event and event.selection else []
    if points:
        cd = points[0].get("customdata")
        if cd is not None and len(cd):
            picked = d[d.event_id == int(cd[0])]
            if len(picked):
                row = picked.iloc[0]
                bill = " · ".join(esc(b) for b in bill_for(artist_events, int(row.event_id)))
                st.markdown(
                    f'<div class="mini-card"><div class="k">{esc(artist_name)} — time #{int(row.appearance_no)}</div>'
                    f'<div class="event-date">{fmt_date(row.event_date).upper()}</div>'
                    f'<div class="event-title">{esc(row.venue)} · {esc(place_line(row.city, row.state_region))}</div>'
                    f'<div class="event-bill">Listed bill: {bill}</div></div>',
                    unsafe_allow_html=True,
                )


def _history_sections(d: pd.DataFrame, artist_events: pd.DataFrame) -> None:
    """NEXT TIME (full tickets) then THE HISTORY (torn, chronological)."""
    chron = d.sort_values(["event_date", "event_id"]).reset_index(drop=True)
    meta_map = {int(r.event_id): f"TIME #{i}" for i, r in enumerate(chron.itertuples(), start=1)}
    ahead = d[d.is_upcoming == 1]
    past = d[d.is_upcoming == 0]
    if len(ahead):
        st.markdown('<div class="eyebrow" style="margin-top:1.2rem">Next time</div>', unsafe_allow_html=True)
        render_ticket_list(ahead, artist_events, limit=10, newest_first=False,
                           variant="upcoming_full", meta_map=meta_map)
    if len(past):
        with st.expander(f"The history — all {len(past)} past times, chronologically"):
            render_ticket_list(past, artist_events, limit=300, newest_first=False,
                               variant="journey_compact", meta_map=meta_map)


def render_profile(
    artist_id: int,
    name: str,
    filtered_events: pd.DataFrame,
    artist_events: pd.DataFrame,
    rich: bool,
) -> None:
    """filtered_events: time-filtered events for this artist only."""
    if filtered_events.empty:
        st.info("No appearances in the current time filter. Widen the time window to see this artist.")
        return
    _hero(name, filtered_events, artist_events)

    d = filtered_events.sort_values(["event_date", "event_id"])
    years_active = set(d.event_date.dt.year.dropna().astype(int))
    first_y, latest_y = min(years_active), max(years_active)
    st.markdown(year_strip_html(first_y, latest_y, years_active), unsafe_allow_html=True)

    if not rich:
        _history_sections(d, artist_events)
        return

    # A. Journey map
    st.markdown('<div class="eyebrow" style="margin-top:1.2rem">Journey map</div>', unsafe_allow_html=True)
    cagg = city_aggregates(d, artist_events)
    fig = city_map(cagg, height=420)
    if fig is not None:
        st.plotly_chart(fig, width="stretch", key=f"profile_map_{artist_id}")
        unplotted = cagg[cagg.latitude.isna()]
        if len(unplotted):
            st.caption(f"{len(unplotted)} places have no resolved coordinates yet and are not plotted.")
    else:
        st.caption("No resolved coordinates for these places yet — run the geocoding workflow to light up this map.")

    # B. Relationship timeline
    st.markdown('<div class="eyebrow" style="margin-top:1.2rem">Every time — click a dot</div>', unsafe_allow_html=True)
    _timeline(name, d, artist_events)

    ret = longest_gap_return(d)
    gap = longest_gap_days(d)
    if ret is not None and gap > 0:
        st.markdown('<div class="eyebrow" style="margin-top:.6rem">Return after the longest gap</div>',
                    unsafe_allow_html=True)
        st.markdown(ticket_html(ret, bill_for(artist_events, int(ret.event_id)), "journey_compact"),
                    unsafe_allow_html=True)
    streak = consecutive_year_streak(d)
    st.markdown(
        f'<p class="small muted">Longest run: seen in <b>{streak}</b> consecutive '
        f'{"year" if streak == 1 else "years"} · longest gap between times: <b>{gap:,}</b> days.</p>',
        unsafe_allow_html=True,
    )

    # C. Analytical cuts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="eyebrow">By place</div>', unsafe_allow_html=True)
        st.markdown(bar_rows_html(cagg.assign(label=cagg.city), "label", "shows"), unsafe_allow_html=True)
        st.markdown('<div class="eyebrow" style="margin-top:1rem">By year</div>', unsafe_allow_html=True)
        yc = year_counts(d)
        st.markdown(bar_rows_html(yc.sort_values("year"), "year", "shows", limit=40), unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="eyebrow">By venue</div>', unsafe_allow_html=True)
        vagg = venue_aggregates(d, artist_events)
        st.markdown(bar_rows_html(vagg.assign(label=vagg.venue), "label", "shows"), unsafe_allow_html=True)
        st.markdown('<div class="eyebrow" style="margin-top:1rem">By decade</div>', unsafe_allow_html=True)
        dc = decade_counts(d)
        dc["label"] = dc.decade.astype(int).astype(str) + "s"
        st.markdown(bar_rows_html(dc.sort_values("decade"), "label", "shows"), unsafe_allow_html=True)

    st.markdown('<div class="eyebrow" style="margin-top:1.2rem">Shared bills</div>', unsafe_allow_html=True)
    st.caption(SHARED_BILLS_CAVEAT)
    co = coappearances(artist_events[artist_events.event_id.isin(d.event_id)], artist_id)
    st.markdown(bar_rows_html(co, "display_name", "shared_bills", limit=12), unsafe_allow_html=True)

    # Rooms and eras
    st.markdown('<div class="eyebrow" style="margin-top:1.2rem">Rooms and eras</div>', unsafe_allow_html=True)
    regions = region_summary(d)
    if len(regions):
        rows = "".join(
            f"<tr><td>{esc(r.state_region)}</td><td style='text-align:right'>{r.first_year}</td>"
            f"<td style='text-align:right'>{r.latest_year}</td>"
            f"<td style='text-align:right'>{r.appearances}</td></tr>"
            for r in regions.itertuples()
        )
        st.markdown(
            "<table style='width:100%;font-size:.88rem;border-collapse:collapse'>"
            "<tr style='color:var(--muted);text-transform:uppercase;font-size:.7rem;letter-spacing:.12em'>"
            "<th style='text-align:left'>Region</th><th style='text-align:right'>First</th>"
            "<th style='text-align:right'>Latest</th><th style='text-align:right'>Times seen</th></tr>"
            f"{rows}</table>",
            unsafe_allow_html=True,
        )

    _history_sections(d, artist_events)
