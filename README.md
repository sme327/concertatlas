# My Concert Atlas
A personal concert atlas — a visual autobiography in shows.

~30 years of shows explored through **place**, **artist**, and **time** on one
map-driven interface — including a chronological **journey player** that
replays your attendance history across the map, one ticket at a time.

## Setup and launch

On macOS, double-click `run.command`, or:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## The data pipeline

```
shows-concerts.csv  →  cleaned SQLite (data/concerts.sqlite)  →  Streamlit app
                          ↑ geocode cache        ↑ reviewed alias table
```

- **654 events** (1995-08-31 → 2026-12-05, including upcoming shows)
- **962 artist identities** after applying the reviewed alias table
- **1,772 event–artist listings** in recorded billing order
- **95 cities · 221 venues**

Ingestion happened upstream and is deterministic; the database ships in `data/`.
Two maintenance scripts modify it, both idempotent:

### Geocoding (cached, reviewed, never invented)

```bash
python scripts/geocode_locations.py   # queries OSM Nominatim, ~1.1s per lookup
# review data/geocoded_locations.csv and data/geocode_review.csv
# put corrections in data/geocode_manual_overrides.csv
python scripts/apply_geocodes.py      # writes coordinates into SQLite
```

Anything unresolved is simply not plotted and is listed on **About the Data**.
No coordinate is ever fabricated. The `Atlantic Ocean` rows (a cruise) are
deliberately unplottable.

### Artist aliases (reviewed, never automatic)

`data/artist_aliases.csv` holds the approved merges — "&"/"and" variants and
clear typos only. Distinct festival years (Outside Lands 2014 vs 2016…) are
never merged. Apply with:

```bash
python scripts/apply_artist_aliases.py
```

## The journey player

In **Follow an Artist** (and for a single selected year), the Atlas swaps the
interactive Plotly map for a client-side journey player with a
`JOURNEY | ALL LOCATIONS` toggle. Playback moves through events in attendance
order: the route accumulates, repeated places pulse and show visit counts, and
a box-office detail card follows along. Controls: Prev · Play/Pause · Next ·
Restart · 1×/2×/4× speed · timeline scrubber (all keyboard accessible;
`prefers-reduced-motion` disables animation but keeps playback working).

> The route is **your sequence of attendance**, never the artist's tour.

**Venues are the destination, not cities.** Every marker, the accumulated
route, and the vehicle's target use the validated venue coordinate when one
resolves, falling back to the trusted city point otherwise
(`journey_sequence`'s `dest_latitude`/`dest_longitude`). Arrival names the
venue directly on the map (not only on the ticket) and settles into a still
hold — no orbiting camera — while it sinks in.

**Every trip leaves home and returns home.** When `data/home_residences.csv`
is filled in (`start_date,city,state_region,note` — one row per era, blank
`start_date` on the first row means "since before the data began"), each
transition bends through that show's home point: previous venue → home →
next venue, with a brief still beat at home. The first stop departs from
home; finishing the journey eases back home once more to close the loop.
Home markers are a stable, unpulsing anchor, distinct from the venue dots
that accumulate and grow with visits. Without a residence file, travel is
just a direct venue-to-venue path, unchanged from before.

The completed path stays visible like a travel diary: earlier segments fade to
~38% opacity, the active segment draws brighter, and when playback ends the
map remains a summary of the whole relationship. Markers encode **concert
gravity** — near-constant size with color intensity (pale amber → deep
orange) and glow scaled to how often a place appears in the selected dataset;
the same encoding is used on the interactive Plotly maps. The detail card
surfaces data-derived milestones ("First Seattle show", "12th time in
Chicago", "First time at Metro"). The artist stays visually present
throughout travel via a monogram badge on the vehicle, derived from their own
displayed name — never a scraped or fabricated photo.

The camera is deliberately simple: one bounds-fit per transition (not one per
leg, regardless of how many waypoints it has), and exactly two framing
states — a calm, flat, wide frame for home and travel, and one tilted,
closer frame that celebrates the arriving venue. There's no per-venue-type
zoom table and no special-cased camera-follow for long flights.

- **MapLibre GL JS is vendored locally** (`assets/vendor/`) and inlined into
  the component — the player code works offline; the vector basemap tiles
  (OpenFreeMap) still need an internet connection, with an automatic
  fallback to a raster Carto style if vector tiles can't load.
- **The player must be served as a real file, never inline HTML.** The
  vendored MapLibre build never loads any vector tiles when its document's
  location is the special `about:srcdoc` value — which is how Streamlit
  embeds a raw HTML string passed to `st.iframe()`. Markers still animate in
  that case (they're plain DOM elements) but the basemap stays permanently
  black. `render_journey_player()` writes the player to `static/` under a
  content-hash filename and points `st.iframe()` at that URL instead, which
  requires `enableStaticServing = true` in `.streamlit/config.toml` (already
  set). See the module docstring in `src/components/journey.py` for how this
  was diagnosed.
- All playback state lives inside the component; Streamlit only supplies the
  ordered journey data (`analytics.journey_sequence`).

## Tickets

Events render as original box-office tickets (one renderer, three variants):
complete printed tickets with an ADMIT ONE stub for **Still Ahead** shows,
torn faded stubs for **From the Archive**, and a slim compact strip for dense
chronologies. Every printed field derives from real event data — the archive
number is the event id; no seat/row/price data is ever invented.

## Architecture

```
app.py                     The Atlas: one map that changes modes (explore/journey)
pages/1_Artists.py         Directory + rich profiles (top 30) / basic profiles
pages/2_Shows.py           Searchable archive of event cards + CSV utility
pages/3_About_the_Data.py  Provenance, coverage, review queues
src/
  config.py                Paths, palette, constants
  state.py                 Central selection model shared by every page
  filters.py               One filtered event set drives all numbers
  analytics.py             Aggregations, streaks, gaps, co-appearances
  repository.py            SQLite → pandas frames
  formatting.py            Dates, spans, derived sentences
  journey_meta.py          Travel-mode/season/venue-category inference, home residences
  ui.py                    CSS system, event cards, constellation, strips
  components/
    map_view.py            Plotly MapLibre city/venue maps + click handling
    journey.py             Client-side journey player (vendored MapLibre)
    artist_browser.py       Searchable chip-grid artist picker (Follow an Artist)
    time_controls.py       ALL TIME | TIMELINE (single year drags into range)
    venue_panel.py         Venue drawer with artist constellation
    event_cards.py         Ticket list + Still Ahead / From the Archive sections
    artist_profile.py      Rich and basic artist profiles
assets/vendor/             Locally vendored maplibre-gl.js / .css (BSD-3)
scripts/                   Geocoding + alias maintenance
tests/                     Analytics, filters, database invariants, boot checks
```

## Data assumptions

- Each nonblank source row is one event; `source_row` traces back to the CSV.
- The `Show` column is the event title and first listing; `is_event_title`
  does **not** mean confirmed headliner.
- Lineup columns are ordered billed names; nothing is inferred about
  opener/headliner/collaboration.
- Upcoming status is recomputed from today's date on every load.

## Optional personal-history files

Two CSVs in `data/` are entirely optional and never fabricated when absent
or incomplete — the app just falls back to simpler behavior:

- **`data/home_residences.csv`** — `start_date,city,state_region,note`, one
  row per place you lived, sorted by date; a blank `start_date` on the first
  row means "since before the data began." Powers the journey player's
  leaving-home/returning-home routing. City/state must already resolve in
  the `cities` table (city-level precision only — no street addresses are
  used or needed).
- **`data/attendance_types.csv`** — `event_id,attendance_type` (one of
  `solo`, `couple`, `friends`, `family`, `festival`). Drives the optional
  small crowd that gathers at arrival in the journey player. Unknown values
  are ignored, never guessed.

## Known limitations

- Some venues (historical rooms, festivals grounds) may not geocode; they are
  reported on About the Data and reachable through lists rather than pins.
- Venue identity is the exact cleaned venue/city/state combination; renamed
  venues appear as separate rooms until an alias is reviewed.
- Built for desktop first; controls remain usable at narrower widths.

## Tests

```bash
pytest -q
```

Covers filtering (year, range, artist+time, place), aggregations, streaks and
gaps, co-appearance counts, upcoming identification, unresolved-coordinate
behavior, database invariants (no orphans, aliases applied, no unexplained
coordinates), and a boot check for every page.
