# CLAUDE.md — My Concert Atlas

Read `PHASE_1_BRIEF.md` and `README.md` before editing. Phase 1 (atlas,
drilldown, profiles, geocoding), Phase 2 (journey player, tickets, narrative
terminology), and Phase 3 (venues-as-destination, home-based routing,
purpose-built artist browser) are complete.

## First actions

1. Run `pytest -q` (40 tests: analytics, filters, journey, tickets, DB invariants, boot checks).
2. Launch with `streamlit run app.py`.
3. Report what works and what you intend to change before broad edits.

## Architecture facts

- Interactive exploration map: Plotly `go.Scattermap` in `src/components/map_view.py`;
  click selection via `on_select="rerun"` + `customdata`, guarded by the
  `map_nonce` key pattern in `src/state.py`. Do not break this path.
- Journey playback: `src/components/journey.py` — a self-contained client-side
  component (vendored MapLibre in `assets/vendor/`, vector tiles from
  OpenFreeMap online, raster Carto fallback). All playback state lives in the
  component; Streamlit supplies only `analytics.journey_sequence()` output
  plus optional home-residence data. Keep it that way.
  - MUST be served via `st.iframe(url)` pointing at a real file in `static/`
    (`_write_static_html`), never `st.iframe(raw_html_string)`. The vendored
    MapLibre build never loads vector tiles when the document location is
    `about:srcdoc` (confirmed by direct testing) — the map goes permanently
    black while markers, which are plain DOM elements, keep animating fine.
    Requires `enableStaticServing = true` in `.streamlit/config.toml`
    (restarting the process, not just refreshing the browser, is required
    for that config change to take effect).
  - Venues are the destination: every marker/route/travel target uses
    `dest_latitude`/`dest_longitude` (validated venue, city fallback), never
    the plain city coordinates directly.
  - Home routing: when `data/home_residences.csv` is filled in, every
    transition bends previous-venue → home → next-venue. `src/journey_meta.py`
    resolves which residence era applies to a date; coordinates always come
    from the trusted `cities` table (`repository.city_coordinates`), never a
    second source.
  - Camera is deliberately two states only (home/travel: flat+wide; arrival:
    tilted+close) — don't reintroduce per-venue-category zoom tables or
    distance-conditional camera-follow branches; that complexity was
    intentionally removed.
- Shared filter state: `src/state.py` session-state model; every number derives
  from one filtered frame (`src/filters.filter_events`).
- Tickets: single renderer `src/ui.ticket_html` with variants
  `upcoming_full | past_torn | journey_compact`. Never add fabricated
  seat/section/row/price/gate data (tests enforce this).
- Artist selection: `src/components/artist_browser.py`, a searchable chip
  grid (never a plain `st.selectbox` — a prior version of that had a real
  bug where `index=0` silently pre-selected the #1 artist without updating
  app state; see git history / memory for the full story).

## Data rules

- Never infer that `is_event_title` means confirmed headliner.
- Never fabricate coordinates; unresolved locations stay listed, not plotted.
- Never silently merge identities; use the reviewed alias table
  (`data/artist_aliases.csv` + `scripts/apply_artist_aliases.py`).
- Upcoming status is recomputed from today's date at load.
- The journey route is the user's attendance order, never an artist's tour —
  keep that sentence near playback controls.

## Branding & terminology

- Product name: **MY CONCERT ATLAS** (renamed from The Long Encore per the homepage brief).
- Times Seen · Places (world level) · Venues · Shared Bills (with the
  "billing roles are not inferred" caveat) · First/Latest/Next Time ·
  Still Ahead · From the Archive.
