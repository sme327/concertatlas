"""The Plotly click-selection path must stay intact: map_nonce invalidates
stale widget selections whenever the selection state changes."""
from streamlit.testing.v1 import AppTest


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
    at.session_state["selected_artist"] = int(
        [sb for sb in at.selectbox if sb.label == "Artist"][0].options[0]
    ) if any(sb.label == "Artist" for sb in at.selectbox) else None
    if at.session_state["selected_artist"] is None:
        return
    at.run()
    assert not at.exception
