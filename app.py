"""The Atlas — home page. One map that changes modes: interactive exploration
in place mode, chronological journey playback for a selected artist or year."""
from __future__ import annotations

import streamlit as st

import random

import plotly.graph_objects as go

from src.analytics import (
    HOME_STATES,
    US_STATES,
    artist_summary,
    city_aggregates,
    country_for_region,
    geo_metrics,
    journey_sequence,
    month_breakdown,
    venue_aggregates,
    year_breakdown,
)
from src.components.artist_browser import render_artist_browser
from src.components.journey import render_journey_player
from src.components.map_view import HOVER_STYLE
from src.config import DATA_DIR, INK, MUTED
from src.filters import bill_for
from src.journey_meta import load_attendance_types, load_home_residences
from src.ui import ticket_html
from src.components.map_view import city_map, clicked_id, venue_map
from src.components.time_controls import render_time_controls
from src.components.venue_panel import render_venue_panel
from src.filters import filter_events
from src.formatting import esc, fmt_date, year_span
from src.repository import artist_frame, city_coordinates, event_frame
from src.state import (
    clear_city,
    init_state,
    prune_empty_selections,
    reset_all,
    select_city,
    select_venue,
    set_mode,
    year_bounds,
)
from src.ui import bar_rows_html, inject_css, page_header

st.set_page_config(page_title="My Concert Atlas", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()


@st.cache_data
def load_data():
    return event_frame(), artist_frame()


@st.cache_data
def load_city_coordinates():
    return city_coordinates()


events, artist_events = load_data()
min_year, max_year = int(events.event_date.dt.year.min()), int(events.event_date.dt.year.max())
init_state(min_year, max_year)
s = st.session_state
summary_all = artist_summary(artist_events)
artist_names = dict(zip(summary_all.artist_id, summary_all.display_name))

page_header()

# ---------------------------------------------------------------- controls
hc1, hc2 = st.columns([1.15, 1.6])
with hc1:
    mode_choice = st.segmented_control(
        "Mode", options=["EXPLORE PLACES", "FOLLOW AN ARTIST"],
        default="FOLLOW AN ARTIST" if s.mode == "artist" else "EXPLORE PLACES",
        label_visibility="collapsed",
    )
    if mode_choice:
        set_mode("artist" if mode_choice == "FOLLOW AN ARTIST" else "place")
with hc2:
    render_time_controls("atlas")

if s.mode == "artist":
    render_artist_browser(summary_all, current=s.selected_artist)

start_year, end_year = year_bounds()
filtered = filter_events(
    events, artist_events,
    start_year=start_year, end_year=end_year,
    artist_id=s.selected_artist if s.mode == "artist" else None,
)
for note in prune_empty_selections(filtered):
    st.caption(note)

if filtered.empty:
    st.warning("Nothing matches the current combination of artist and time. "
               "Widen the time window or clear the artist to get your world back.")
    st.button("Reset the Atlas", on_click=reset_all)
    st.stop()

upcoming_n = int(filtered.is_upcoming.sum())
cagg = city_aggregates(filtered, artist_events)

# ---------------------------------------------------------------- view mode
# The journey player replaces the normal map in journey states; a toggle
# keeps the interactive Plotly map one click away.
drilled = s.selected_city is not None or s.selected_venue is not None
artist_journey = s.mode == "artist" and s.selected_artist is not None
year_journey = s.mode == "place" and s.time_mode == "range" and start_year == end_year
journey_available = (artist_journey or year_journey) and not drilled

view = "ALL LOCATIONS"
if journey_available:
    view = st.segmented_control(
        "View", options=["JOURNEY", "ALL LOCATIONS"],
        default="JOURNEY" if artist_journey else "ALL LOCATIONS",
        label_visibility="collapsed",
    ) or "ALL LOCATIONS"

if journey_available and view == "JOURNEY":
    # ------------------------------------------------------------ journey
    stops = journey_sequence(
        filtered, artist_events,
        attendance_types=load_attendance_types(DATA_DIR / "attendance_types.csv"),
        home_residences=load_home_residences(DATA_DIR / "home_residences.csv"),
        city_coords=load_city_coordinates(),
    )
    if artist_journey:
        title = artist_names.get(s.selected_artist, "")
        # Progressive header: start at the first stop; the player advances it.
        first_year = stops[0]["event_date"][:4] if stops else ""
        subtitle = f"1 TIME SEEN · {first_year}"
        label_mode = "artist"
    else:
        title = f"{start_year} in concert"
        subtitle = f"{len(stops)} shows that year"
        label_mode = "year"
    render_journey_player(stops, esc(title.upper()), esc(subtitle), label_mode=label_mode)
    unmapped = sum(1 for x in stops if not x["has_coords"])
    if unmapped:
        st.caption(f"{unmapped} stop{'s' if unmapped != 1 else ''} in this journey have no resolved "
                   "coordinates; they stay in the chronology without a map point.")
    if artist_journey and st.button("Open full artist profile"):
        s.profile_artist = s.selected_artist
        st.switch_page("pages/1_Artists.py")
else:
    # ------------------------------------------------------------ standard map
    map_col, panel_col = st.columns([2.6, 1], gap="medium")

    with map_col:
        if s.selected_city is not None:
            city_row = cagg[cagg.city_id == s.selected_city].iloc[0]
            bc1, bc2 = st.columns([0.26, 1])
            with bc1:
                st.button("← All places", on_click=clear_city)
            with bc2:
                st.markdown(
                    f'<div class="panel-sub" style="padding-top:.45rem">'
                    f'<b style="color:var(--paper)">{esc(city_row.city)}</b> · '
                    f'{int(city_row.shows)} shows in {int(city_row.venues)} rooms</div>',
                    unsafe_allow_html=True,
                )
            vagg = venue_aggregates(filtered, artist_events, s.selected_city)
            fig = venue_map(vagg, s.selected_venue, height=600)
            if fig is not None:
                event = st.plotly_chart(fig, width="stretch", on_select="rerun",
                                        selection_mode=("points",), key=f"atlas_map_{s.map_nonce}")
                cid = clicked_id(event)
                if cid is not None and cid != s.selected_venue:
                    select_venue(cid)
                    st.rerun()
                unplotted = vagg[vagg.latitude.isna()]
                if len(unplotted):
                    st.caption(f"{len(unplotted)} venues here have no resolved coordinates yet — "
                               "open them from the list on the right. Details in About the Data.")
            else:
                st.info("No venue in this city has resolved coordinates yet. "
                        "Use the venue list on the right; run the geocoding workflow to light up this map.")
        else:
            fig = city_map(cagg, height=600)
            if fig is not None:
                event = st.plotly_chart(fig, width="stretch", on_select="rerun",
                                        selection_mode=("points",), key=f"atlas_map_{s.map_nonce}")
                cid = clicked_id(event)
                if cid is not None and cid != s.selected_city:
                    select_city(cid)
                    st.rerun()
                unplotted = cagg[cagg.latitude.isna()]
                if len(unplotted):
                    st.caption(f"{len(unplotted)} places have no resolved coordinates and are not "
                               "plotted — open them from the list on the right. Details in About the Data.")
            else:
                st.info("The map is waiting for coordinates. Run `python scripts/geocode_locations.py`, "
                        "review the cache, then `python scripts/apply_geocodes.py`.")
                st.image("assets/concert-map-square.png", width="stretch",
                         caption="Visual direction for the concert atlas")
        single_year = s.time_mode == "range" and start_year == end_year
        if single_year:
            # One year selected: the year histogram would be a single bar, so
            # show that year month by month instead (informative, not clickable).
            mb = month_breakdown(filtered, artist_events)
            if len(mb):
                colors = ["#b4553f" if up else "#e89a3d" for up in mb.has_upcoming.astype(bool)]
                bar = go.Figure(go.Bar(
                    x=mb.label, y=mb.shows, marker_color=colors, marker_line_width=0,
                    customdata=mb[["top_artist", "top_venue"]].fillna("—").values,
                    hovertemplate=("<b>%{x} " + str(start_year) + "</b> · %{y} shows<br>"
                                   "Top artist: %{customdata[0]}<br>"
                                   "Top venue: %{customdata[1]}<extra></extra>"),
                ))
                bar.update_layout(
                    height=120, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor=INK, plot_bgcolor=INK,
                    xaxis=dict(color=MUTED, tickfont=dict(size=9), showgrid=False,
                               categoryorder="array", categoryarray=mb.label.tolist()),
                    yaxis=dict(visible=False), hoverlabel=HOVER_STYLE, showlegend=False, bargap=0.25,
                )
                st.plotly_chart(bar, width="stretch", key=f"monthbar_{s.map_nonce}")
                st.caption(f"{start_year}, month by month. Widen the timeline above to compare years.")
            yb = year_breakdown(filtered, artist_events).head(0)  # skip year chart below
        else:
            # Timeline histogram: hover for the year's top artist/venue; click a
            # bar to focus the whole page on that year; future shows read warm red.
            yb = year_breakdown(filtered, artist_events)
        if len(yb):
            in_filter = (yb.year >= start_year) & (yb.year <= end_year) if s.time_mode == "range" \
                else yb.year.notna()
            colors = ["#b4553f" if up else ("#e89a3d" if sel else "#6b5136")
                      for up, sel in zip(yb.has_upcoming.astype(bool), in_filter)]
            bar = go.Figure(go.Bar(
                x=yb.year, y=yb.shows, marker_color=colors, marker_line_width=0,
                customdata=yb[["top_artist", "top_venue"]].fillna("—").values,
                hovertemplate=("<b>%{x}</b> · %{y} shows<br>Top artist: %{customdata[0]}<br>"
                               "Top venue: %{customdata[1]}<extra></extra>"),
            ))
            bar.update_layout(
                height=120, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor=INK, plot_bgcolor=INK,
                xaxis=dict(color=MUTED, tickfont=dict(size=9), dtick=5, showgrid=False),
                yaxis=dict(visible=False), hoverlabel=HOVER_STYLE, showlegend=False, bargap=0.25,
            )
            bar_event = st.plotly_chart(bar, width="stretch", on_select="rerun",
                                        selection_mode=("points",), key=f"yearbar_{s.map_nonce}")
            bar_points = bar_event.selection.points if bar_event and bar_event.selection else []
            if bar_points:
                clicked_year = int(bar_points[0]["x"])
                if not (s.time_mode == "range" and start_year == end_year == clicked_year):
                    s.time_mode = "range"
                    s.start_year = s.end_year = s.year = clicked_year
                    from src.state import bump_map_nonce
                    bump_map_nonce()
                    st.rerun()

    with panel_col:
        if s.selected_venue is not None:
            vagg_all = venue_aggregates(filtered, artist_events, s.selected_city)
            vrow = vagg_all[vagg_all.venue_id == s.selected_venue]
            if len(vrow):
                render_venue_panel(vrow.iloc[0], filtered, artist_events)
        elif s.selected_city is not None:
            city_row = cagg[cagg.city_id == s.selected_city].iloc[0]
            vagg = venue_aggregates(filtered, artist_events, s.selected_city)
            st.markdown(
                f'<div class="side-panel">'
                f'<div class="panel-title">{esc(city_row.city)}</div>'
                f'<div class="panel-sub">{esc(city_row.state_region)}</div>'
                f'<div class="stat-line"><span>Shows</span><b>{int(city_row.shows)}</b></div>'
                f'<div class="stat-line"><span>Venues</span><b>{int(city_row.venues)}</b></div>'
                f'<div class="stat-line"><span>Artists</span><b>{int(city_row.artists)}</b></div>'
                f'<div class="stat-line"><span>First show</span><b>{fmt_date(city_row.first_date)}</b></div>'
                f'<div class="stat-line"><span>Latest show</span><b>{fmt_date(city_row.latest_date)}</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="eyebrow" style="margin-top:.8rem">The rooms</div>', unsafe_allow_html=True)
            st.markdown(bar_rows_html(vagg.assign(label=vagg.venue), "label", "shows", limit=12),
                        unsafe_allow_html=True)
            venue_ids = vagg.venue_id.tolist()
            venue_names = dict(zip(vagg.venue_id, vagg.venue))
            venue_shows = dict(zip(vagg.venue_id, vagg.shows))

            def _open_venue():
                if s.open_venue_sel is not None:
                    select_venue(int(s.open_venue_sel))
                    s.open_venue_sel = None   # action select: reset to placeholder

            s.open_venue_sel = None
            st.selectbox("Open a venue", venue_ids, key="open_venue_sel",
                         format_func=lambda i: f"{venue_names[i]} — {venue_shows[i]}×",
                         placeholder="Open a venue…", on_change=_open_venue,
                         label_visibility="collapsed")
        elif artist_journey:
            name = artist_names.get(s.selected_artist, "")
            others = artist_events[(artist_events.event_id.isin(filtered.event_id))
                                   & (artist_events.artist_id != s.selected_artist)]
            past = filtered[filtered.is_upcoming == 0].sort_values("event_date")
            ahead = filtered[filtered.is_upcoming == 1].sort_values("event_date")
            first_line = latest_line = next_line = ""
            if len(past):
                fr, lr = past.iloc[0], past.iloc[-1]
                first_line = (f'<div class="stat-line"><span>First time</span>'
                              f'<b>{esc(fr.city)} · {fr.event_date:%Y}</b></div>')
                latest_line = (f'<div class="stat-line"><span>Latest time</span>'
                               f'<b>{esc(lr.city)} · {lr.event_date:%Y}</b></div>')
            if len(ahead):
                nr = ahead.iloc[0]
                next_line = (f'<div class="stat-line"><span>Next time</span>'
                             f'<b>{esc(nr.city)} · {fmt_date(nr.event_date)}</b></div>')
            st.markdown(
                f'<div class="side-panel">'
                f'<div class="panel-title">{esc(name)}</div>'
                f'<div class="panel-sub">Your history with this artist</div>'
                f'<div class="stat-line"><span>Times seen</span><b>{len(filtered):,}</b></div>'
                f'<div class="stat-line"><span>Places</span><b>{filtered.city_id.nunique()}</b></div>'
                f'<div class="stat-line"><span>Venues</span><b>{filtered.venue_id.nunique()}</b></div>'
                f'<div class="stat-line"><span>Shared bills</span><b>{others.artist_id.nunique():,}</b></div>'
                f'{first_line}{latest_line}{next_line}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption("Shared bills counts names listed for the same events; billing roles are not inferred.")
            if st.button("Open full artist profile"):
                s.profile_artist = s.selected_artist
                st.switch_page("pages/1_Artists.py")
        else:
            n_artists = artist_events[artist_events.event_id.isin(filtered.event_id)].artist_id.nunique()
            gm = geo_metrics(filtered)
            upcoming_line = (f'<div class="stat-line"><span>Still ahead</span><b>{upcoming_n}</b></div>'
                             if upcoming_n else "")
            st.markdown(
                f'<div class="side-panel">'
                f'<div class="panel-title">AT A GLANCE</div>'
                f'<div class="stat-line"><span>Shows</span><b>{len(filtered):,}</b></div>'
                f'<div class="stat-line"><span>Venues</span><b>{filtered.venue_id.nunique()}</b></div>'
                f'<div class="stat-line"><span>Artists</span><b>{n_artists:,}</b></div>'
                f'<div class="stat-line"><span>States</span><b>{gm["states"]}</b></div>'
                f'<div class="stat-line"><span>Countries</span><b>{gm["countries"]}</b></div>'
                f'{upcoming_line}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="eyebrow" style="margin-top:.8rem">Most visited</div>', unsafe_allow_html=True)
            mv = st.segmented_control(
                "Most visited", options=["Cities", "Venues", "States", "Countries"],
                default="Cities", key="mv_toggle", label_visibility="collapsed",
            ) or "Cities"
            if mv == "Cities":
                ranked = [(f"{r.city} · {r.state_region}", int(r.shows))
                          for r in cagg.head(8).itertuples()]
            elif mv == "Venues":
                vagg_all = venue_aggregates(filtered, artist_events)
                ranked = [(f"{r.venue} · {r.city}", int(r.shows))
                          for r in vagg_all.head(8).itertuples()]
            elif mv == "States":
                states = (filtered[filtered.state_region.isin(US_STATES - HOME_STATES)]
                          .groupby("state_region").event_id.nunique()
                          .sort_values(ascending=False).head(8))
                ranked = list(states.items())
            else:
                by_country = filtered.assign(country=filtered.state_region.map(country_for_region))
                countries = (by_country.dropna(subset=["country"])
                             .groupby("country").event_id.nunique()
                             .sort_values(ascending=False).head(8))
                ranked = list(countries.items())
            if mv == "States":
                st.caption("Home states (IL, CA, WA) excluded.")
            ranks = "".join(
                f'<div class="rank-row"><span>{i}. {esc(label)}</span>'
                f'<span class="n">{n}</span></div>'
                for i, (label, n) in enumerate(ranked, start=1)
            ) or '<div class="muted small">Nothing in this filter.</div>'
            st.markdown(ranks, unsafe_allow_html=True)
            city_ids = cagg.city_id.tolist()
            city_names = dict(zip(cagg.city_id, cagg.city))
            city_shows = dict(zip(cagg.city_id, cagg.shows))

            def _open_place():
                if s.open_place_sel is not None:
                    select_city(int(s.open_place_sel))
                    s.open_place_sel = None   # action select: reset to placeholder

            s.open_place_sel = None
            st.selectbox("Open a place", city_ids, key="open_place_sel",
                         format_func=lambda i: f"{city_names[i]} — {city_shows[i]} shows",
                         placeholder="Open a place…", on_change=_open_place,
                         label_visibility="collapsed")

if s.time_mode == "range":
    # ------------------------------------------------------------ the stubs
    # Timeline view: the page becomes those years — every ticket stub from
    # the selected window, chronological. Upcoming/random sections step aside.
    chron = filtered.sort_values(["event_date", "event_id"])
    if len(chron):
        st.divider()
        label = str(start_year) if start_year == end_year else f"{start_year}–{end_year}"
        st.markdown(
            f'<div class="eyebrow">The stubs — {label} · {len(chron)} night'
            f'{"s" if len(chron) != 1 else ""}</div>',
            unsafe_allow_html=True,
        )
        grid = "".join(
            ticket_html(row, bill_for(artist_events, row.event_id), "journey_compact")
            for row in chron.itertuples()
        )
        st.markdown(f'<div class="ticket-grid">{grid}</div>', unsafe_allow_html=True)
else:
    # ------------------------------------------------------------ still ahead
    # Every upcoming show, always — a responsive grid, never a truncated list.
    ahead = filtered[filtered.is_upcoming == 1].sort_values(["event_date", "event_id"])
    if len(ahead):
        st.divider()
        st.markdown(
            f'<div class="eyebrow">Still ahead — {len(ahead)} night'
            f'{"s" if len(ahead) != 1 else ""} on the horizon</div>',
            unsafe_allow_html=True,
        )
        grid = "".join(
            ticket_html(row, bill_for(artist_events, row.event_id), "journey_compact")
            for row in ahead.itertuples()
        )
        st.markdown(f'<div class="ticket-grid">{grid}</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------ one night at random
    # A memory resurfaced from the archive — an invitation to keep exploring
    # broadly. Place mode only: while following one artist, every ticket is
    # already that artist's, so a "random" pull adds nothing new to discover.
    past = filtered[filtered.is_upcoming == 0]
    if s.mode == "place" and len(past):
        st.divider()
        mc1, mc2 = st.columns([2.2, 1], vertical_alignment="center")
        with mc1:
            st.markdown('<div class="eyebrow">One night at random</div>', unsafe_allow_html=True)
        with mc2:
            if st.button("Pull another from the shoebox"):
                s.memory_seed = s.get("memory_seed", 0) + 1
        memory_id = random.Random(s.get("memory_seed", 0)).choice(sorted(past.event_id.tolist()))
        memory = past[past.event_id == memory_id].iloc[0]
        n_here = int(filtered[filtered.venue_id == memory.venue_id].event_id.nunique())
        meta = f"ONE OF {n_here} NIGHTS AT {str(memory.venue).upper()}" if n_here > 1 else ""
        st.markdown(ticket_html(memory, bill_for(artist_events, int(memory.event_id)),
                                "past_torn", meta=meta), unsafe_allow_html=True)
        if st.button("Visit this venue on the map"):
            set_mode("place")
            select_city(int(memory.city_id))
            select_venue(int(memory.venue_id))
            st.rerun()
