# The Long Encore — Streamlit Concert Atlas
## Phase 1 Implementation Brief

Build a polished local Streamlit application from `shows-concerts.csv`. The app is a personal interactive concert atlas covering approximately 655 events from 1995 through 2026.

The central experience is not a generic dashboard. It is a map-driven way to explore the same concert history through three connected dimensions:

- Place
- Artist
- Time

The application should feel like a modern interactive music publication: dark, warm, personal, visually intentional, and fun to explore.

---

# Product Vision

The first version should not be a collection of dashboard pages with a map added. It should be an **interactive concert atlas**, where **place, time, and artist are three interchangeable ways to explore the same history**.

The app has two primary exploration modes:

## Explore a Place

Start broad, choose a city, move into its venue landscape, and discover who was seen in each room.

## Follow an Artist

Choose Counting Crows—or another frequently seen artist—and watch the map reduce itself to that artist’s path through the user’s life.

A shared time control alters either experience:

- All time
- A specific year
- A custom date range
- Life chapters in a later phase

The core interaction model is:

> **Where? Who? When?**

Every view should answer some combination of those three questions.

---

# Product Principles

1. The map is the primary interface, not a supplemental chart.
2. Place, artist, and time filters must update the same underlying event set.
3. Every claim must be derived from the source data.
4. Preserve ambiguous source meanings instead of inventing certainty.
5. Do not assume the first artist column always represents a confirmed headliner.
6. Do not fabricate map coordinates.
7. Favor visual discovery over raw tables.
8. Build a maintainable application rather than a one-file prototype.
9. The interface should feel like a personal music archive, not Tableau.
10. The map, venue drawer, artist filter, and time filter must behave as one coherent system.

---

# Site Structure

Keep Version 1 focused on four pages:

```text
THE ATLAS
ARTISTS
SHOWS
ABOUT THE DATA
```

The Atlas is the home page. A separate dashboard is not required for Phase 1.

---

# 1. The Atlas

This is the default home page.

Provide two exploration modes:

```text
EXPLORE PLACES | FOLLOW AN ARTIST
```

Provide a persistent time control:

```text
ALL TIME | YEAR | RANGE
```

## Default View: My Concert World

Initially display one marker per concert city.

Marker size should reflect the number of matching events.

Hover information should include:

- City
- Number of shows
- Number of venues
- Number of distinct artists
- First show date
- Latest show date

The initial map should immediately establish the geography of the concert history, including major locations such as Chicago, Seattle, San Francisco, Oakland, Milwaukee, and other cities present in the data.

## Contextual Side Panel

A compact panel beside the map should update with the current filter state.

Example all-time content:

```text
MY CONCERT WORLD

655 shows
94 cities
217 venues
1995–2026

Most visited
1. Chicago — 303
2. Seattle — 62
3. San Francisco — 42
```

This panel must not be a static leaderboard. When a location, artist, or time period changes, its contents should change too.

---

## Explore Places: City Drilldown

Selecting a city should switch the map from city level to venue level and frame the selected city.

For Chicago, the map should display venue pins for places such as:

- Metro
- House of Blues
- Riviera
- Aragon Ballroom
- Vic
- Lincoln Hall
- Schubas
- Double Door
- Park West
- Grant Park
- Every other Chicago venue in the data

The user should feel as though they are looking at **their version of the city**, defined by the rooms where music happened.

### Venue Marker Encoding

- Pin size = number of matching shows
- Pin emphasis = selected venue
- Optional subtle outer rings = distinct years attended
- Hover = venue, visits, artists, and date range
- Click = open venue-detail drawer

Do not create multiple literal pins at identical venue coordinates for individual shows. They will overlap and become unusable. Use one venue pin containing the accumulated history, then reveal individual shows within the venue detail.

---

## Venue Detail Drawer

Selecting a venue should open a persistent panel or expandable drawer beside the map.

Example:

```text
METRO
Chicago, Illinois

49 shows · 1996–2026
83 artists encountered
```

Display:

- Venue name
- City and region
- Total matching shows
- Number of distinct artists
- First visit
- Latest visit
- Artist appearance summary
- Compact year history
- Chronological event history in an expandable section

### Artist Constellation

Rather than beginning with a plain list, display artists as a visual field or ranked collection containing:

- Artist name
- Number of appearances at the venue
- First and latest year seen there
- Small year dots or a horizontal span
- Stronger visual weight for artists seen there more frequently
- An action to select the artist and switch into artist exploration

Example:

```text
Jimmy Eat World          7 appearances    ● 1999 ● 2001 ● 2004 ...
Motion City Soundtrack   5 appearances    ● 2003 ● 2005 ...
Counting Crows           3 appearances    ● 1996 ● 1999 ● 2008
```

The chronological show list should be available below, but it should be secondary and collapsible.

### Venue History Strip

Include a compact timeline from the first visit through the latest visit:

```text
1996 ━━━●━━●━━━━●━━━●━━━━━━●━━ 2026
```

Selecting or hovering over a year should reveal matching events when practical.

---

# 2. Time as a Universal Layer

Time should alter the entire site rather than exist only as an isolated analytics page.

## All Time

Display the complete geography.

## Single Year

Provide a year selector or slider.

Example:

```text
1995 ━━━━━━━━━●━━━━━━━━ 2026
              2009
```

When 2009 is selected:

- Only cities visited in 2009 remain active
- City marker sizes reflect show count during 2009
- A city map shows only venues attended during 2009
- Venue details show only artists and events from 2009
- Artist profiles and summary metrics recalculate for 2009

## Custom Range

Provide a dual-ended year control.

Example:

```text
2006 ├━━━━━━━━━━━━━━┤ 2011
```

This allows meaningful stretches of time without requiring formal life chapters in Phase 1.

## Playback

Animated year-by-year map playback is a later-phase feature. Do not make it a Phase 1 requirement. Filtering must first be reliable, fast, and visually clear.

---

# 3. Follow an Artist

The Atlas needs an artist-focused mode using the same map and interaction language.

## Artist Selector

Provide search across all artists while initially emphasizing the 30 most frequently seen.

Selecting an artist should update the map so that:

- Only cities where that artist was seen remain active
- City marker size reflects appearances for the selected artist
- Selecting a city reveals only venues where the artist was seen
- Venue marker size reflects appearances at each venue
- The side panel shows the artist’s complete geographic journey

## Artist Map Path

An optional line may connect locations chronologically when it remains meaningful and readable.

It must be labeled clearly as:

> Your sequence of seeing this artist

It must not imply the performer’s tour route.

---

# 4. Artists

Create a browsable artist directory.

Default ordering:

1. Most appearances
2. Artist name

Support:

- Search
- Minimum-appearance filtering
- Quick selection of the top 30 repeat artists

The top 30 artists should receive rich profile pages. Every other artist should receive a basic functional profile.

---

## Rich Artist Profile

### Artist Hero

Example:

```text
COUNTING CROWS

43 appearances
1996–2026
12 cities · 19 venues
```

Add a short sentence derived only from confirmed data, such as:

> You have seen Counting Crows across 30 years, from your Chicago years through California and into Seattle.

Do not fabricate genres, tours, setlists, or qualitative opinions.

### A. Journey Map

Embed the artist-filtered map.

Show:

- Every city
- Venue-level detail after city selection
- Number of appearances at each location
- First and latest appearance
- Time filtering

### B. Relationship Timeline

Display every appearance on a horizontal timeline.

Example:

```text
1996  ●
1997       ● ●
1999             ●
2000               ● ● ●
...
2026                                      ●
```

Selecting a point should reveal:

- Date
- Venue
- City
- Full listed bill
- Numbered occurrence of seeing the artist

Example:

```text
COUNTING CROWS — APPEARANCE #17
August 12, 2008
Ravinia · Highland Park, Illinois
```

### C. Analytical Cuts

Each top artist profile should include:

#### By City

Where the artist was seen most often.

#### By Venue

Which venues are most central to the personal history with the artist.

#### By Year

Concentrated runs, quiet periods, and returns.

#### By Decade

A simple historical distribution.

#### By Co-Appearance

Artists most frequently appearing on the same event rows.

Use careful wording:

> Artists appearing on the same listed bills

Do not infer opener, headliner, or collaboration unless the source data explicitly establishes it.

#### First, Latest, and Longest-Gap Return

Create three event cards:

- First appearance
- Most recent appearance
- Return after the longest gap

#### Longest Streak

Examples:

- Seen in four consecutive years
- Seen six times over 18 months
- Longest gap between appearances

#### Rooms and Eras

Provide a location summary such as:

| Place | First | Latest | Appearances |
|---|---:|---:|---:|
| Chicago area | 1996 | 2010 | 25 |
| California | 2012 | 2019 | 10 |
| Seattle area | 2022 | 2026 | 8 |

Actual regions must be calculated from the data. Do not hardcode the example values.

### Full Chronological History

Include every matching event in chronological order.

---

# 5. Shows

Create a dependable searchable archive beneath the more creative views.

## Filters

- Date or year range
- Artist
- Venue
- City
- State or region
- Completed versus upcoming
- Multi-artist event
- Search text

## Event Cards

Use compact designed event cards rather than a raw Streamlit dataframe.

Example:

```text
AUG 31, 1995

LIVE
New World Music Theatre
Tinley Park, Illinois

Live · PJ Harvey · Veruca Salt
```

Selecting a card should reveal the full listed bill and links or actions for:

- View venue
- View city
- View artist
- Previous show
- Next show

A dataframe or CSV download may exist as a secondary utility inside an expander, but it should not define the page.

---

# 6. About the Data

Explain:

- Source file
- Number of parsed events
- Date coverage
- Meaning of event title versus artist listing
- Normalization rules
- Geocoding coverage
- Unresolved cities or venues
- Known ambiguities
- Upcoming-event handling

Display or link to a data-quality review table.

---

# Source Data Structure

The CSV contains:

- `in FB`
- `Date`
- `Venue`
- `City`
- `State`
- `Show`
- Additional artist columns named `Unnamed: 6` through `Unnamed: 23`

Treat each nonblank source row as one event.

Treat `Show` and every populated `Unnamed:*` field as ordered event-title or artist entries.

Convert the wide artist columns into an event-artist relationship table.

Preserve:

- Original source row
- Original text
- Listing order
- Whether the value came from the `Show` column

Do not label the `Show` value as a confirmed headliner. Store it as `is_event_title` or an equivalent field.

---

# Data Cleanup Requirements

The source is usable but requires a careful deterministic cleanup layer.

## Required Cleanup

- Remove the completely blank trailing row
- Parse all valid dates
- Handle the known date strings that omit expected punctuation
- Normalize whitespace
- Normalize obvious capitalization inconsistencies safely
- Preserve original values alongside cleaned values
- Separate country from state or region where possible
- Support unusual geographic values such as `Atlantic Ocean`
- Flag likely artist or venue spelling variants for review
- Never silently merge uncertain identities

Create a review queue rather than automatically fixing ambiguous records.

Examples of likely review candidates may include misspellings or variant punctuation. A suspicious value should be surfaced for review, not silently rewritten.

---

# Data Model

Use SQLite for the cleaned application data.

## events

```text
event_id
event_date
event_title
venue_id
city_id
facebook_recorded
is_upcoming
source_row
```

## artists

```text
artist_id
display_name
normalized_name
```

## event_artists

```text
event_id
artist_id
billing_order
is_event_title
original_text
```

`is_event_title` does not mean confirmed headliner. It only indicates that the value appeared in the original `Show` column.

## venues

```text
venue_id
venue_name_recorded
canonical_venue_name
city_id
latitude
longitude
geocode_status
```

## cities

```text
city_id
city
state_region
country
latitude
longitude
geocode_status
```

Add useful indexes for:

- Date
- Artist
- Venue
- City
- Upcoming status

The ingestion process must be deterministic and rerunnable.

---

# Geocoding Requirements

Geocoding must be a separate preprocessing workflow. Do not geocode on every Streamlit rerun.

Create:

```text
scripts/geocode_locations.py
data/geocoded_locations.csv
data/geocode_review.csv
```

Suggested coordinate-cache columns:

```text
location_type
canonical_name
venue
city
state_region
country
latitude
longitude
geocode_status
source
review_note
```

## Geocoding Workflow

1. Extract distinct cities and venue/city/region combinations.
2. Reuse cached coordinates.
3. Geocode only new unresolved locations.
4. Apply responsible rate limiting.
5. Record source and result status.
6. Never invent coordinates.
7. Send ambiguous or failed matches to review.
8. Support a manual override file.
9. Allow the Streamlit app to run with partial coordinate coverage.
10. Clearly show unplotted records in About the Data.

Use exact venue and geographic context in geocoding queries.

Preserve historical venue names.

## Venue Identity

Preserve:

```text
venue_name_recorded
```

Also support:

```text
canonical_venue_id
canonical_venue_name
```

Do not automatically merge similarly named venues without a reviewed alias table.

For Phase 1, exact cleaned venue, city, and state combinations may act as venue identities. Add alias resolution only where clearly needed.

---

# Shared Application State

Create a coherent central state model similar to:

```python
{
    "mode": "place" | "artist",
    "selected_artist": None,
    "selected_city": None,
    "selected_venue": None,
    "time_mode": "all" | "year" | "range",
    "start_year": 1995,
    "end_year": 2026,
}
```

All metrics and details must be recalculated from the current filtered event set.

## Expected Behavior

- Selecting a city switches from city map to venue map.
- Clearing a city returns to the broad map.
- Selecting an artist resets incompatible venue selections.
- Artist selection remains active when the time filter changes.
- Time changes preserve other compatible selections.
- If a selected venue becomes empty after filtering, clear it gracefully.
- Empty states should explain what happened and provide a reset.
- Map selection and side-panel selection must stay synchronized.
- Browser-style navigation within Streamlit should remain predictable.

---

# Visual Direction

The site should feel like a modern interactive music feature, not a business dashboard.

## Palette

- Deep charcoal or near-black foundation
- Warm ivory or off-white text
- Amber or orange stage-light accent
- Muted red secondary accent
- Quiet gray map geography
- Selected pins that feel illuminated, not neon

## Interface Details

- Compact uppercase navigation
- Large clear dates and years
- Subtle ticket-stub influence on event cards
- Thin timeline lines
- Pin pulse only for active selection
- Smooth but restrained transitions
- Very few emojis in the application
- Minimal gradients
- No excessive glassmorphism
- Avoid generic white Streamlit boxes
- Avoid placing every section inside bordered cards
- Avoid a wall of generic metric tiles

The map should remain the dominant visual element on the Atlas page.

Use a custom Streamlit theme and targeted CSS, while retaining functional and maintainable native Streamlit controls.

Build primarily for desktop while keeping controls usable at narrower widths.

---

# Suggested Architecture

Use a modular structure similar to:

```text
app.py
pages/
    1_Artists.py
    2_Shows.py
    3_About_the_Data.py
src/
    config.py
    models.py
    ingest.py
    repository.py
    filters.py
    analytics.py
    geocoding.py
    state.py
    formatting.py
    components/
        map_view.py
        time_controls.py
        venue_panel.py
        artist_profile.py
        event_cards.py
data/
scripts/
tests/
```

Keep data access, calculations, filtering, and presentation separate.

Do not place the entire application in `app.py`.

---

# Version 1 Exclusions

Do not include these in Phase 1:

- Spotify integration
- Setlist.fm integration
- Artist images scraped from the internet
- Genre classification
- Ticket uploads
- Photo uploads
- Personal ratings
- Personal memories or notes
- Companion tracking
- Social sharing
- Animated map playback
- Artist relationship network diagrams
- AI-written musical opinions
- Authentication
- Editing source data through the app

These may become later phases, but they should not distract from map exploration, time filtering, venue discovery, and artist deep dives.

---

# Testing Requirements

Add automated tests for at least:

- Blank-row removal
- Date parsing
- Wide-to-long artist conversion
- Artist normalization
- Event counts
- Artist appearance counts
- City aggregation
- Venue aggregation
- Single-year filtering
- Custom-range filtering
- Artist-plus-time filtering
- Longest artist gap
- Consecutive-year streak
- Co-appearance counts
- Upcoming-event identification
- Behavior with unresolved coordinates

Include a lightweight application boot check.

---

# Deliverables

1. Working Streamlit application
2. Deterministic CSV-to-SQLite ingestion
3. Cached geocoding workflow
4. Data-quality review output
5. Automated tests
6. README containing:
   - Setup
   - Ingestion
   - Geocoding
   - Launching
   - Architecture
   - Data assumptions
   - Known limitations
7. Concise implementation summary
8. Screenshots or walkthroughs of:
   - All-city map
   - Chicago venue map
   - Selected Metro panel
   - Counting Crows map
   - Counting Crows profile
   - Year-filtered map

---

# Acceptance Criteria

The first pass is successful only when:

1. The app boots locally with one documented command.
2. Every valid CSV event is represented.
3. Artists from all populated lineup columns are normalized into an event-artist relationship table.
4. The default map displays every successfully geocoded concert city.
5. Selecting Chicago reveals its venue map.
6. Selecting a venue reveals matching artists and shows.
7. A time filter updates map markers, counts, venue details, and artist details consistently.
8. Selecting Counting Crows displays only their concert geography.
9. The top 30 artists receive rich deep-dive profiles.
10. Every other artist receives a functional basic profile.
11. No location is plotted using fabricated coordinates.
12. Missing coordinates appear in a review report.
13. The interface does not rely primarily on raw dataframes.
14. Upcoming shows are visually distinguishable from completed shows.
15. Every statistic is date-bounded and derived from the filtered event set.
16. Automated tests cover parsing, filtering, location aggregation, and artist-profile calculations.
17. The README explains architecture, geocoding cache, assumptions, limitations, and launch process.
18. The final interface feels like a personal concert atlas rather than a generic analytics dashboard.

---

# Final Implementation Direction

Begin by inspecting the source CSV and repository environment.

Before changing code:

1. Report the detected row count, date range, artist-column structure, unique cities, unique venues, and likely cleanup issues.
2. Propose the exact implementation sequence.
3. Identify any mapping-library or geocoding choices and explain why.
4. Confirm which coordinates are resolved, unresolved, or uncertain.
5. Then implement the application in phases.

Do not expand the product scope until these four systems work reliably together:

- Map exploration
- Venue detail
- Artist filtering and profiles
- Universal time filtering

Once those foundations are stable, later features such as life chapters, ticket images, setlists, memories, companions, and animated playback can be layered onto the same model.
