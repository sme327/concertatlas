"""Apply the reviewed artist alias table to the SQLite database.

Reads data/artist_aliases.csv (only rows with approved == "yes") and remaps
event_artists rows from each variant artist to its canonical artist. The
original recorded text is already preserved in event_artists.original_text,
so no source information is lost. Variant artist rows that no longer have
any event references are removed.

The script is idempotent and safe to rerun.

Usage: python scripts/apply_artist_aliases.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "concerts.sqlite"
ALIASES = DATA / "artist_aliases.csv"


def main() -> None:
    aliases = pd.read_csv(ALIASES)
    aliases = aliases[aliases.approved.astype(str).str.lower() == "yes"]
    conn = sqlite3.connect(DB)
    merged = 0
    for _, row in aliases.iterrows():
        variant = conn.execute(
            "SELECT artist_id FROM artists WHERE display_name = ?", (row.variant_name,)
        ).fetchone()
        canonical = conn.execute(
            "SELECT artist_id FROM artists WHERE display_name = ?", (row.canonical_name,)
        ).fetchone()
        if variant is None:
            continue  # already merged on a previous run
        if canonical is None:
            # Canonical spelling never appeared on its own: rename the variant.
            conn.execute(
                "UPDATE artists SET display_name = ?, normalized_name = ? WHERE artist_id = ?",
                (row.canonical_name, row.canonical_name.lower(), variant[0]),
            )
            merged += 1
            continue
        if variant[0] == canonical[0]:
            continue
        conn.execute(
            "UPDATE event_artists SET artist_id = ? WHERE artist_id = ?",
            (canonical[0], variant[0]),
        )
        conn.execute("DELETE FROM artists WHERE artist_id = ?", (variant[0],))
        merged += 1
    conn.commit()
    remaining = conn.execute("SELECT count(*) FROM artists").fetchone()[0]
    conn.close()
    print(f"Applied {merged} alias merges; {remaining} artist identities remain.")


if __name__ == "__main__":
    main()
