from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "concerts.sqlite"
ASSETS_DIR = ROOT / "assets"

TOP_ARTIST_COUNT = 30

# Palette — deep charcoal foundation, warm ivory text, amber stage light.
INK = "#0C1012"
PANEL = "#111719"
PAPER = "#EEE7DA"
MUTED = "#A6AAA7"
AMBER = "#E89A3D"
AMBER_DIM = "rgba(232, 154, 61, 0.55)"
RED = "#B4553F"
LINE = "#343A3B"

MAP_STYLE = "carto-darkmatter"
