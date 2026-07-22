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
    .homemarker, .crowdwrap, .flourish): animation/rotation must only
    target inner elements."""
    assert ".lemarker.current.pulse .dot { animation:lepulse" in PLAYER_CSS
    assert ".lemarker.current.pulse {" not in PLAYER_CSS
    for selector in (".lemarker {", ".veh {", ".crowdwrap {", ".homemarker {"):
        root_block = PLAYER_CSS.split(selector)[1].split("}")[0]
        assert "transform" not in root_block and "animation" not in root_block, selector
    assert '<div class="dot"></div>' in PLAYER_JS
    assert "querySelector('.dot')" in PLAYER_JS
    assert "icon.style.transform" in PLAYER_JS       # inner .veh-icon
    assert "el.style.transform" not in PLAYER_JS     # marker roots untouched
    # The arrival flourish uses CSS class toggling (.in) for its fade/rise,
    # not a transform assigned from JS — the marker root stays untouched.
    assert "fel.classList.add('in')" in PLAYER_JS
    assert "fel.style.transform" not in PLAYER_JS


def test_cinematic_structure():
    """Travel and arrival are choreographed, calm, and resilient."""
    for needle in ["async function travelAnim", "async function arrivalAnim",
                   "contrail", "trailFeatures", "SEASON_PARK", "RASTER_STYLE",
                   "STREET_OK", "fill-extrusion", "CROWD_SIZE"]:
        assert needle in PLAYER_JS
    # Crowds only appear when attendance metadata exists — never invented.
    assert "CROWD_SIZE[s.attendance_type]" in PLAYER_JS
    # Reduced motion skips travel/pan animation but playback still works.
    assert "if (RM) return;" in PLAYER_JS
    assert "const pts = waypoints.filter(Boolean);" in PLAYER_JS


def test_camera_simplified_to_two_states():
    """'Simplify the camera': no per-venue-category zoom table, no
    long-flight camera-follow special case — one arrival zoom/pitch pair
    for precise (venue) vs city-level framing, one travel-fit per
    transition regardless of how many legs it has."""
    assert "CATEGORY_ZOOM" not in PLAYER_JS
    assert "follow = " not in PLAYER_JS and "map.jumpTo({ center: pos" not in PLAYER_JS
    assert "async function travelAnim(waypoints" in PLAYER_JS


def test_home_routing_present():
    """Every trip leaves home and returns home when home data is configured;
    falls back to a direct venue-to-venue path when it isn't."""
    assert "function transitionWaypoints" in PLAYER_JS
    assert "function homeOf(s)" in PLAYER_JS
    assert "async function finishJourney()" in PLAYER_JS
    assert "addHomeMarkers" in PLAYER_JS


def test_venues_are_the_destination_not_cities():
    """Markers, trails, and travel targets all key off dest_* (validated
    venue, falling back to the trusted city point) rather than the plain
    city coordinates directly."""
    assert "function destOf(s)" in PLAYER_JS
    assert "s.dest_latitude" in PLAYER_JS
    assert "s.city_latitude" not in PLAYER_JS  # never read directly client-side


def test_band_presence_derived_not_fabricated():
    """The artist badge is a monogram derived from the artist's own
    (already-displayed) name — never a scraped or invented image."""
    assert "BAND_INITIAL" in PLAYER_JS
    assert "jtitle').textContent" in PLAYER_JS
    assert "veh-badge" in PLAYER_JS and "veh-badge" in PLAYER_CSS


def test_no_fabricated_fields_in_player_card():
    for forbidden in ("SEAT", "SECTION", "GATE", "PRICE"):
        assert forbidden not in PLAYER_JS.upper().replace("ALSO LISTED", "")
