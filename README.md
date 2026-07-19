# The Long Encore
### A Personal Concert Atlas

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

The completed path stays visible like a travel diary: earlier segments fade to
~38% opacity, the active segment draws brighter, and when playback ends the
map remains a summary of the whole relationship. Markers encode **concert
gravity** — near-constant size with color intensity (pale amber → deep
orange) and glow scaled to how often a place appears in the selected dataset;
the same encoding is used on the interactive Plotly maps. The detail card
surfaces data-derived milestones ("First Seattle show", "12th time in
Chicago", "First time at Metro").

- **MapLibre GL JS is vendored locally** (`assets/vendor/`) and inlined into
  the component — the player code works offline.
- **Basemap tiles still come from Carto online** — the map background needs an
  internet connection (same as the Plotly basemap).
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
  ui.py                    CSS system, event cards, constellation, strips
  components/
    map_view.py            Plotly MapLibre city/venue maps + click handling
    journey.py             Client-side journey player (vendored MapLibre)
    time_controls.py       ALL TIME | YEAR | RANGE (universal)
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
