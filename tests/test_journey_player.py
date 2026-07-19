"""Player-logic tests: the progressive header is executed with node exactly as
shipped (HEADER_JS), and the marker DOM convention that fixed the coordinate
drift is asserted so it cannot silently regress."""
import json
import shutil
import subprocess

import pytest

from src.components.journey import HEADER_JS, PLAYER_CSS, PLAYER_JS

node = shutil.which("node")


def run_header_js(stops, checks):
    """Evaluate headerLine(stops, i) for each (i, expected) pair in node."""
    script = (
        HEADER_JS
        + f"\nconst STOPS = {json.dumps(stops)};\n"
        + "\n".join(
            f"""(() => {{
  const got = headerLine(STOPS, {i});
  const want = {json.dumps(expected)};
  if (got !== want) {{ console.error('stop {i}: got ' + got + ' want ' + want); process.exit(1); }}
}})();"""
            for i, expected in checks
        )
        + "\nconsole.log('OK');\n"
    )
    out = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "OK" in out.stdout


def stops_for(dates):
    return [{"event_date": d} for d in dates]


@pytest.mark.skipif(node is None, reason="node not available")
def test_progressive_header_counts_and_spans():
    stops = stops_for(["1997-03-10", "1997-07-05", "2003-05-01", "2008-08-12", "2026-08-07"])
    run_header_js(stops, [
        (0, "1 TIME SEEN · 1997"),          # first stop, singular
        (1, "2 TIMES SEEN · 1997"),         # same-year progress, one year shown
        (2, "3 TIMES SEEN · 1997–2003"),    # span opens when a later year is reached
        (3, "4 TIMES SEEN · 1997–2008"),    # mid-journey
        (4, "5 TIMES SEEN · 1997–2026"),    # final stop includes upcoming year only now
    ])


@pytest.mark.skipif(node is None, reason="node not available")
def test_upcoming_year_not_shown_before_reached():
    stops = stops_for(["2019-08-09", "2026-08-07"])
    run_header_js(stops, [(0, "1 TIME SEEN · 2019"), (1, "2 TIMES SEEN · 2019–2026")])


def test_header_updates_wired_to_every_control_path():
    """prev/next/restart/scrubber/play all funnel through show() → rebuild()
    → renderCard(), which is the single place the header is written; the
    cinematic play loop advances via show() too."""
    assert "function show(i, animate) { idx = Math.max(0, Math.min(i, N-1)); rebuild(idx, animate); }" in PLAYER_JS
    assert PLAYER_JS.count("headerLine(STOPS") == 1  # written only in renderCard
    assert "renderCard(s);" in PLAYER_JS             # called from rebuild
    assert "show(j, false);" in PLAYER_JS            # runPlay advances through show()
    for control in ["scrub.oninput", "getElementById('prev')", "getElementById('nextb')",
                    "getElementById('restart')", "async function runPlay"]:
        assert control in PLAYER_JS


def test_marker_transform_regression_guard():
    """MapLibre owns the root transform on every marker (.lemarker, .veh,
    .crowdwrap): animation/rotation must only target inner elements."""
    assert ".lemarker.current.pulse .dot { animation:lepulse" in PLAYER_CSS
    assert ".lemarker.current.pulse {" not in PLAYER_CSS
    root_block = PLAYER_CSS.split(".lemarker {")[1].split("}")[0]
    assert "transform" not in root_block and "animation" not in root_block
    assert '<div class="dot"></div>' in PLAYER_JS
    assert "querySelector('.dot')" in PLAYER_JS
    # Vehicle rotation and crowd motion live on inner elements, never roots.
    veh_root = PLAYER_CSS.split(".veh {")[1].split("}")[0]
    crowd_root = PLAYER_CSS.split(".crowdwrap {")[1].split("}")[0]
    assert "transform" not in veh_root and "transform" not in crowd_root
    assert "icon.style.transform" in PLAYER_JS       # inner .veh-icon
    assert "el.style.transform" not in PLAYER_JS     # marker roots untouched


def test_cinematic_structure():
    """Travel and arrival are choreographed, calm, and resilient."""
    for needle in ["async function travelAnim", "async function arrivalAnim",
                   "contrail", "trailFeatures", "SEASON_PARK", "RASTER_STYLE",
                   "STREET_OK", "fill-extrusion", "CROWD_SIZE"]:
        assert needle in PLAYER_JS
    # Crowds only appear when attendance metadata exists — never invented.
    assert "CROWD_SIZE[s.attendance_type]" in PLAYER_JS
    # Reduced motion skips travel animation but playback still works.
    assert "if (RM || !a || !b || !mode) return;" in PLAYER_JS


def test_no_fabricated_fields_in_player_card():
    for forbidden in ("SEAT", "SECTION", "GATE", "PRICE"):
        assert forbidden not in PLAYER_JS.upper().replace("ALSO LISTED", "")
