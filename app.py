"""The Atlas — home page. One map that changes modes: interactive exploration
in place mode, chronological journey playback for a selected artist or year."""
from __future__ import annotations

import streamlit as st

from src.analytics import artist_summary, city_aggregates, journey_sequence, venue_aggregates, year_counts
from src.components.event_cards import render_archive_sections
from src.components.journey import render_journey_player
from src.components.map_view import city_map, clicked_id, venue_map
from src.components.time_controls import render_time_controls
from src.components.venue_panel import render_venue_panel
from src.filters import filter_events
from src.formatting import esc, fmt_date, year_span
from src.repository import artist_frame, event_frame
from src.state import (
    clear_city,
    init_state,
    prune_empty_selections,
    reset_all,
    select_artist,
    select_city,
    select_venue,
    set_mode,
    year_bounds,
)
from src.ui import bar_rows_html, inject_css, journey_timeline_html, page_header

st.set_page_config(page_title="The Long Encore — Atlas", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()


@st.cache_data
def load_data():
    return event_frame(), artist_frame()


events, artist_events = load_data()
min_year, max_year = int(events.event_date.dt.year.min()), int(events.event_date.dt.year.max())
init_state(min_year, max_year)
s = st.session_state
summary_all = artist_summary(artist_events)
artist_names = dict(zip(summary_all.artist_id, summary_all.display_name))
artist_counts = dict(zip(summary_all.artist_id, summary_all.appearances))

page_header(f"{min_year}–{max_year}")

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
    ids = summary_all.artist_id.tolist()
    current = ids.index(s.selected_artist) if s.selected_artist in ids else None
    chosen = st.selectbox(
        "Artist", options=ids, index=current,
        format_func=lambda i: f"{artist_names[i]} — {artist_counts[i]}×",
        placeholder=f"Search {len(ids):,} artists (the most-seen are first)…",
        label_visibility="collapsed",
    )
    if chosen != s.selected_artist:
        select_artist(chosen)

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
year_journey = s.mode == "place" and s.time_mode == "year"
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
    stops = journey_sequence(filtered, artist_events)
    if artist_journey:
        title = artist_names.get(s.selected_artist, "")
        # Progressive header: start at the first stop; the player advances it.
        first_year = stops[0]["event_date"][:4] if stops else ""
        subtitle = f"1 TIME SEEN · {first_year}"
        label_mode = "artist"
    else:
        title = f"{s.year} in concert"
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
        # Chronological journey strip: the same filtered history, year by year.
        yc = year_counts(filtered)
        strip = journey_timeline_html(yc, s.year if s.time_mode == "year" else None)
        if strip:
            st.markdown(strip, unsafe_allow_html=True)

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
            pick = st.selectbox("Open a venue", venue_ids, index=None,
                                format_func=lambda i: f"{venue_names[i]} — {venue_shows[i]}×",
                                placeholder="Open a venue…", label_visibility="collapsed")
            if pick is not None:
                select_venue(int(pick))
                st.rerun()
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
            upcoming_line = (f'<div class="stat-line"><span>Still ahead</span><b>{upcoming_n}</b></div>'
                             if upcoming_n else "")
            st.markdown(
                f'<div class="side-panel">'
                f'<div class="panel-title">MY CONCERT WORLD</div>'
                f'<div class="panel-sub">Everything, everywhere, so far</div>'
                f'<div class="stat-line"><span>Shows</span><b>{len(filtered):,}</b></div>'
                f'<div class="stat-line"><span>Places</span><b>{filtered.city_id.nunique()}</b></div>'
                f'<div class="stat-line"><span>Venues</span><b>{filtered.venue_id.nunique()}</b></div>'
                f'<div class="stat-line"><span>Artists</span><b>{n_artists:,}</b></div>'
                f'<div class="stat-line"><span>Span</span><b>'
                f'{year_span(filtered.event_date.min(), filtered.event_date.max())}</b></div>'
                f'{upcoming_line}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="eyebrow" style="margin-top:.8rem">Most visited</div>', unsafe_allow_html=True)
            ranks = "".join(
                f'<div class="rank-row"><span>{i}. {esc(r.city)} · '
                f'<span class="muted">{esc(r.state_region)}</span></span>'
                f'<span class="n">{int(r.shows)}</span></div>'
                for i, r in enumerate(cagg.head(8).itertuples(), start=1)
            )
            st.markdown(ranks, unsafe_allow_html=True)
            city_ids = cagg.city_id.tolist()
            city_names = dict(zip(cagg.city_id, cagg.city))
            city_shows = dict(zip(cagg.city_id, cagg.shows))
            pick = st.selectbox("Open a place", city_ids, index=None,
                                format_func=lambda i: f"{city_names[i]} — {city_shows[i]} shows",
                                placeholder="Open a place…", label_visibility="collapsed")
            if pick is not None:
                select_city(int(pick))
                st.rerun()

# ---------------------------------------------------------------- tickets
st.divider()
render_archive_sections(filtered, artist_events)
