"""The Plotly click-selection path must stay intact: map_nonce invalidates
stale widget selections whenever the selection state changes."""
import sqlite3
from pathlib import Path

from streamlit.testing.v1 import AppTest

DB = Path(__file__).resolve().parents[1] / "data" / "concerts.sqlite"


def _any_artist_id() -> int:
    with sqlite3.connect(DB) as c:
        return c.execute("select artist_id from artists limit 1").fetchone()[0]


def test_map_nonce_bumps_on_selection_changes():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    nonce0 = at.session_state["map_nonce"]

    open_city = [sb for sb in at.selectbox if sb.label == "Open a place"][0]
    city_id = open_city.options[0]
    open_city.select(city_id)
    at.run()
    assert not at.exception
    assert at.session_state["selected_city"] is not None
    assert at.session_state["map_nonce"] > nonce0

    nonce1 = at.session_state["map_nonce"]
    at.session_state["time_mode"] = "range"
    at.session_state["start_year"] = 2000
    at.session_state["end_year"] = 2010
    at.run()
    assert not at.exception


def test_journey_view_defaults_for_artist_mode():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["mode"] = "artist"
    at.session_state["selected_artist"] = _any_artist_id()
    at.run()
    assert not at.exception


def test_artist_browser_does_not_auto_select_on_mode_switch():
    """Regression coverage for a real bug in the previous plain-selectbox
    picker: st.selectbox defaulted to index=0, and since the artist list is
    sorted by appearances, the #1 most-seen artist became the widget's
    value the instant Follow an Artist opened — without selected_artist
    ever updating, since on_change only fires on a genuine change. That
    silently left the page on the place-mode view (Still Ahead / One Night
    at Random) while looking like an artist was already picked, and no
    journey map ever appeared.

    The purpose-built browser (a button grid) can't default-select at all —
    nothing is "clicked" until a real click happens — but this test keeps
    driving the real widgets (segmented_control + button), not hand-set
    state, so any future regression of this shape gets caught the same way.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.segmented_control[0].set_value("FOLLOW AN ARTIST").run()
    assert not at.exception, at.exception

    assert at.session_state["selected_artist"] is None
    body = " ".join(m.value for m in at.markdown)
    assert "Most followed" in body  # the browsable grid, not a dropdown
    assert "One night at random" not in body

    # A real chip click must select the artist and enter journey mode.
    top_chip = [b for b in at.button if b.key and b.key.startswith("ab_top_")][0]
    top_chip.click().run()
    assert not at.exception, at.exception
    assert isinstance(at.session_state["selected_artist"], int)
    journey_toggles = [sc for sc in at.segmented_control if sc.options == ["JOURNEY", "ALL LOCATIONS"]]
    assert journey_toggles, "journey/all-locations toggle must appear once an artist is picked"
    body = " ".join(m.value for m in at.markdown)
    assert "One night at random" not in body
