"""About the Data — provenance, meaning, coverage, and known ambiguities."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DATA_DIR
from src.repository import artist_frame, event_frame, geocode_coverage, unresolved_locations
from src.ui import inject_css, page_header

st.set_page_config(page_title="About · My Concert Atlas", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()
page_header()


@st.cache_data
def load_data():
    return event_frame(), artist_frame()


events, artist_events = load_data()

st.markdown('<div class="eyebrow">Provenance and limitations</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">ABOUT THE DATA</div>', unsafe_allow_html=True)

upcoming = int(events.is_upcoming.sum())
st.write(
    f"The archive is built from a single source spreadsheet (`shows-concerts.csv`) and contains "
    f"**{len(events):,} events** with **{artist_events.artist_id.nunique():,} artist identities** and "
    f"**{len(artist_events):,} event–artist listings**, spanning "
    f"**{events.event_date.min():%B %Y} – {events.event_date.max():%B %Y}**. "
    f"**{upcoming}** events are upcoming (dated after today) and are marked as such throughout the site."
)

st.markdown("""
#### What the fields mean

- Each nonblank source row is one event. The original row number is preserved as `source_row`.
- The source `Show` column is preserved as the **event title** and as the first ordered listing.
  `is_event_title` does **not** assert a headliner — only that the value came from that column.
- The additional lineup columns are preserved as **ordered billed names**; order of listing is kept,
  and nothing is inferred about opener/headliner/collaboration relationships.
- Whether a show was recorded on Facebook is kept in `facebook_recorded`.

#### Normalization rules

- Dates are parsed deterministically; whitespace and obvious capitalization issues are cleaned,
  with the original text always preserved alongside.
- Artist names are normalized only for identity matching; the displayed name keeps its recorded form.
- A small **reviewed alias table** (`data/artist_aliases.csv`) merges unambiguous variants —
  "&"/"and" spellings and clear typos (e.g. *Tom Petty & the Heartbrakers*). Distinct festival years
  (e.g. *Outside Lands 2014* vs *2016*) are deliberately **not** merged.
- Uncertain identities are never silently merged; they stay in the review queue below.
""")

st.markdown("#### Geocoding coverage")
st.write(
    "Coordinates come from a cached OpenStreetMap Nominatim workflow "
    "(`scripts/geocode_locations.py` → review → `scripts/apply_geocodes.py`). "
    "No coordinate is ever invented; anything unresolved is simply not plotted and is listed here."
)
coverage = geocode_coverage()
pivot = coverage.pivot_table(index="location_type", columns="status", values="n", fill_value=0)
st.dataframe(pivot, width="stretch")

unresolved = unresolved_locations()
if len(unresolved):
    st.markdown(f"**{len(unresolved)} locations have no resolved coordinates** and appear on no map:")
    st.dataframe(unresolved, hide_index=True, width="stretch")
else:
    st.success("Every city and venue currently has resolved coordinates.")

review_file = DATA_DIR / "geocode_review.csv"
if review_file.exists():
    review = pd.read_csv(review_file)
    if len(review):
        with st.expander(f"Geocode review queue ({len(review)} entries)"):
            st.dataframe(review, hide_index=True, width="stretch")

st.markdown("#### Known ambiguities and the review queue")
st.write(
    "Suspicious values are surfaced for review rather than silently rewritten. "
    "This includes possible spelling variants that were **not** merged, and source rows "
    "with missing venue or city values (e.g. the Atlantic Ocean cruise rows, which have "
    "no fixed coordinates by nature)."
)
audit_path = DATA_DIR / "data_quality_review.csv"
if audit_path.exists():
    st.dataframe(pd.read_csv(audit_path), hide_index=True, width="stretch")

aliases_path = DATA_DIR / "artist_aliases.csv"
if aliases_path.exists():
    with st.expander("Reviewed alias table (applied merges)"):
        st.dataframe(pd.read_csv(aliases_path), hide_index=True, width="stretch")
