# CLAUDE.md — The Long Encore (A Personal Concert Atlas)

Read `PHASE_1_BRIEF.md` and `README.md` before editing. Phase 1 (atlas,
drilldown, profiles, geocoding) and Phase 2 (journey player, tickets,
narrative terminology) are complete.

## First actions

1. Run `pytest -q` (40 tests: analytics, filters, journey, tickets, DB invariants, boot checks).
2. Launch with `streamlit run app.py`.
3. Report what works and what you intend to change before broad edits.

## Architecture facts

- Interactive exploration map: Plotly `go.Scattermap` in `src/components/map_view.py`;
  click selection via `on_select="rerun"` + `customdata`, guarded by the
  `map_nonce` key pattern in `src/state.py`. Do not break this path.
- Journey playback: `src/components/journey.py` — a self-contained client-side
  component (vendored MapLibre in `assets/vendor/`, inlined; Carto tiles online).
  All playback state lives in the component; Streamlit supplies only
  `analytics.journey_sequence()` output. Keep it that way.
- Shared filter state: `src/state.py` session-state model; every number derives
  from one filtered frame (`src/filters.filter_events`).
- Tickets: single renderer `src/ui.ticket_html` with variants
  `upcoming_full | past_torn | journey_compact`. Never add fabricated
  seat/section/row/price/gate data (tests enforce this).

## Data rules

- Never infer that `is_event_title` means confirmed headliner.
- Never fabricate coordinates; unresolved locations stay listed, not plotted.
- Never silently merge identities; use the reviewed alias table
  (`data/artist_aliases.csv` + `scripts/apply_artist_aliases.py`).
- Upcoming status is recomputed from today's date at load.
- The journey route is the user's attendance order, never an artist's tour —
  keep that sentence near playback controls.

## Branding & terminology

- Product name: **THE LONG ENCORE**, subtitle "A Personal Concert Atlas".
- Times Seen · Places (world level) · Venues · Shared Bills (with the
  "billing roles are not inferred" caveat) · First/Latest/Next Time ·
  Still Ahead · From the Archive.
