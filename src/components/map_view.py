"""Plotly MapLibre maps for cities and venues.

Both maps encode show counts as marker size, expose ids through customdata
for click selection, and only ever plot rows with resolved coordinates.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.config import AMBER, INK, LINE, MAP_STYLE, MUTED, PAPER
from src.formatting import fmt_date

HOVER_STYLE = dict(bgcolor="#1a2124", bordercolor=LINE, font=dict(color=PAPER, size=13))


def _zoom_for(lats: pd.Series, lons: pd.Series, single_point_zoom: float = 10.5) -> tuple[dict, float]:
    lats, lons = lats.astype(float), lons.astype(float)
    center = dict(lat=float(lats.mean()), lon=float(lons.mean()))
    lat_span = float(lats.max() - lats.min())
    lon_span = float(lons.max() - lons.min())
    span = max(lat_span * 1.35, lon_span, 1e-6)
    if span < 0.02:
        return center, single_point_zoom
    zoom = math.log2(360.0 / span) - 0.4
    return center, max(1.0, min(zoom, 15.0))


def _gravity(shows: pd.Series) -> np.ndarray:
    """Concert gravity 0..1: how central a location is in the current dataset."""
    peak = max(float(shows.max()), 1.0)
    return np.sqrt(shows.astype(float) / peak)


def _gravity_colors(shows: pd.Series) -> list[str]:
    """Density encoding: yellow → orange → red with visit frequency, so the
    busiest place (Chicago) reads as dominant before any number is read."""
    t = _gravity(shows)
    colors = []
    for v in t:
        if v < 0.5:                      # yellow -> orange
            u = v / 0.5
            r, g, b = 242 + (232 - 242) * u, 209 + (140 - 209) * u, 107 + (48 - 107) * u
        else:                            # orange -> red
            u = (v - 0.5) / 0.5
            r, g, b = 232 + (185 - 232) * u, 140 + (48 - 140) * u, 48 + (33 - 48) * u
        colors.append(f"rgb({int(r)},{int(g)},{int(b)})")
    return colors


def _sizes(shows: pd.Series, base: float = 9, spread: float = 17) -> np.ndarray:
    """Size grows meaningfully with visit count so the dominant city reads
    at a glance; color still carries the density scale."""
    return base + _gravity(shows) * spread


def _lightened(colors: list[str], amount: float = 0.45) -> list[str]:
    out = []
    for c in colors:
        r, g, b = (int(x) for x in c[4:-1].split(","))
        out.append(f"rgb({int(r + (255 - r) * amount)},{int(g + (255 - g) * amount)},"
                   f"{int(b + (255 - b) * amount)})")
    return out


def _glow_trace(plot: pd.DataFrame) -> go.Scattermap | None:
    """A warm halo behind the busiest locations. Lightened toward white so it
    reads as glow on the dark basemap, not a muddy stain."""
    t = _gravity(plot.shows)
    hot = plot[t >= 0.5]
    if hot.empty:
        return None
    return go.Scattermap(
        lat=hot.latitude, lon=hot.longitude, mode="markers",
        marker=dict(size=_sizes(hot.shows) * 1.7, color=_lightened(_gravity_colors(hot.shows)),
                    opacity=0.3),
        hoverinfo="skip",
    )


def _base_layout(fig: go.Figure, center: dict, zoom: float, height: int) -> go.Figure:
    fig.update_layout(
        map=dict(style=MAP_STYLE, center=center, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        paper_bgcolor=INK,
        showlegend=False,
        hoverlabel=HOVER_STYLE,
        dragmode="pan",
    )
    return fig


def city_map(cities: pd.DataFrame, height: int = 560) -> go.Figure | None:
    """One marker per city; customdata[0] is city_id for click handling."""
    plot = cities.dropna(subset=["latitude", "longitude"])
    if plot.empty:
        return None
    # Draw ascending so the busiest places paint LAST — Chicago sits on top
    # of its metro neighbors instead of hiding beneath them.
    plot = plot.sort_values("shows")
    center, zoom = _zoom_for(plot.latitude, plot.longitude, single_point_zoom=8.0)
    customdata = np.stack([
        plot.city_id.astype(int), plot.city.astype(str), plot.state_region.astype(str),
        plot.shows.astype(int), plot.venues.astype(int), plot.artists.astype(int),
        plot.first_date.map(fmt_date), plot.latest_date.map(fmt_date),
    ], axis=-1)
    fig = go.Figure()
    glow = _glow_trace(plot)
    if glow is not None:
        fig.add_trace(glow)
    fig.add_trace(go.Scattermap(
        lat=plot.latitude, lon=plot.longitude,
        mode="markers",
        marker=dict(size=_sizes(plot.shows), color=_gravity_colors(plot.shows), opacity=0.95),
        customdata=customdata,
        hovertemplate=(
            "<b>%{customdata[1]}</b> · %{customdata[2]}<br>"
            "%{customdata[3]} shows · %{customdata[4]} venues · %{customdata[5]} artists<br>"
            "%{customdata[6]} — %{customdata[7]}<extra></extra>"
        ),
    ))
    return _base_layout(fig, center, zoom, height)


def venue_map(venues: pd.DataFrame, selected_venue_id: int | None = None, height: int = 560) -> go.Figure | None:
    """One marker per venue within a city; the selected venue is illuminated."""
    plot = venues.dropna(subset=["latitude", "longitude"])
    if plot.empty:
        return None
    plot = plot.sort_values("shows")   # busiest venues paint on top
    center, zoom = _zoom_for(plot.latitude, plot.longitude, single_point_zoom=13.0)

    def trace(rows: pd.DataFrame, selected: bool) -> go.Scattermap:
        customdata = np.stack([
            rows.venue_id.astype(int), rows.venue.astype(str),
            rows.shows.astype(int), rows.artists.astype(int), rows.years.astype(int),
            rows.first_date.map(fmt_date), rows.latest_date.map(fmt_date),
        ], axis=-1)
        return go.Scattermap(
            lat=rows.latitude, lon=rows.longitude,
            mode="markers",
            marker=dict(
                size=_sizes(rows.shows, base=15 if selected else 11, spread=5),
                color="#F5C97E" if selected else _gravity_colors(rows.shows),
                opacity=1.0 if selected else 0.9,
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "%{customdata[2]} shows · %{customdata[3]} artists · %{customdata[4]} years<br>"
                "%{customdata[5]} — %{customdata[6]}<extra></extra>"
            ),
        )

    fig = go.Figure()
    normal = plot if selected_venue_id is None else plot[plot.venue_id != selected_venue_id]
    fig.add_trace(trace(normal, selected=False))
    if selected_venue_id is not None:
        sel = plot[plot.venue_id == selected_venue_id]
        if len(sel):
            fig.add_trace(trace(sel, selected=True))
    return _base_layout(fig, center, zoom, height)


def clicked_id(chart_event) -> int | None:
    """First selected point's customdata id from a st.plotly_chart on_select event."""
    try:
        points = chart_event.selection.points
    except AttributeError:
        points = (chart_event or {}).get("selection", {}).get("points", []) if chart_event else []
    # The glow underlay has no customdata; take the first point that does.
    for point in points or []:
        cd = point.get("customdata")
        if cd is not None and len(cd):
            try:
                return int(cd[0])
            except (TypeError, ValueError):
                continue
    return None
