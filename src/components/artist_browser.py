"""A purpose-built artist browser: a searchable, browsable grid of chips
instead of a plain developer-style dropdown. Most-followed artists are
always one glance away; anyone else is a few keystrokes from appearing in
the same grid. Selecting a chip immediately enters Follow an Artist mode.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.state import select_artist, set_mode

TOP_GRID_COLUMNS = 5
SEARCH_GRID_COLUMNS = 3
SEARCH_RESULT_LIMIT = 24


def _chip_grid(ids: list[int], names: dict[int, str], counts: dict[int, int],
              columns: int, key_prefix: str, current: int | None) -> int | None:
    picked = None
    cols = st.columns(columns)
    for i, artist_id in enumerate(ids):
        col = cols[i % columns]
        label = f"{names[artist_id]}\n{counts[artist_id]}×"
        if col.button(label, key=f"{key_prefix}_{artist_id}",
                     type="primary" if artist_id == current else "secondary",
                     use_container_width=True):
            picked = artist_id
    return picked


def _browser_body(summary_all: pd.DataFrame, current: int | None) -> int | None:
    artist_names = dict(zip(summary_all.artist_id, summary_all.display_name))
    artist_counts = dict(zip(summary_all.artist_id, summary_all.appearances))

    with st.container(key="artist_browser"):
        query = st.text_input(
            "Find an artist", placeholder=f"Search {len(summary_all):,} artists…",
            label_visibility="collapsed", key="artist_browser_query",
        )
        if query:
            matches = summary_all[summary_all.display_name.str.contains(query, case=False, regex=False)]
            ids = matches.artist_id.tolist()
            if not ids:
                st.caption("No artist matches that search.")
                return None
            st.caption(f"{len(ids):,} match{'es' if len(ids) != 1 else ''}"
                      + (f" — showing the first {SEARCH_RESULT_LIMIT}"
                         if len(ids) > SEARCH_RESULT_LIMIT else ""))
            return _chip_grid(ids[:SEARCH_RESULT_LIMIT], artist_names, artist_counts,
                              SEARCH_GRID_COLUMNS, "ab_search", current)
        st.markdown('<div class="eyebrow">Most followed</div>', unsafe_allow_html=True)
        top_ids = summary_all.head(30).artist_id.tolist()
        return _chip_grid(top_ids, artist_names, artist_counts, TOP_GRID_COLUMNS, "ab_top", current)


def render_artist_browser(summary_all: pd.DataFrame, current: int | None) -> None:
    """Renders search + a weighted chip grid; on a pick, immediately enters
    artist mode. Nothing is returned — this mirrors the other click-driven
    selection flows in the app (e.g. the venue drawer's "follow" picker).

    Once an artist is already selected, the grid collapses behind a
    "change artist" expander so the browser doesn't compete for space with
    the journey below it — browsing is still one click away.
    """
    if current is None:
        picked = _browser_body(summary_all, current)
    else:
        name = summary_all.loc[summary_all.artist_id == current, "display_name"]
        label = f"Following {name.iloc[0]} — change artist" if len(name) else "Change artist"
        with st.expander(label):
            picked = _browser_body(summary_all, current)

    if picked is not None:
        set_mode("artist")
        select_artist(picked)
        st.rerun()
