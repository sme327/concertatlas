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


def test_artist_selectbox_does_not_auto_select_on_mode_switch():
    """Regression test for a real bug: st.selectbox defaults to index=0, and
    the artist list is sorted by appearances, so the #1 most-seen artist
    (Counting Crows) would silently become the widget's value the instant
    Follow an Artist is opened — without ever updating selected_artist,
    since on_change only fires on a genuine user change, not on the default.
    That mismatch made the page fall back to the place-mode view (with Still
    Ahead / One Night at Random) while showing what looked like a selected
    artist and no journey map. The fix is index=None on that selectbox;
    this test switches modes via the real widget (not by hand-setting
    session_state) so it actually exercises that default.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.segmented_control[0].set_value("FOLLOW AN ARTIST").run()
    assert not at.exception, at.exception

    artist_box = [sb for sb in at.selectbox if sb.label == "Artist"][0]
    assert artist_box.value is None, "artist selectbox must not auto-select on open"
    assert at.session_state["selected_artist"] is None
    body = " ".join(m.value for m in at.markdown)
    assert "One night at random" not in body

    # A real pick must still work and enter journey mode. AppTest's
    # .options exposes the formatted label; .select() resolves it back to
    # the underlying artist_id, which is what should land in state.
    artist_box.select(artist_box.options[0]).run()
    assert not at.exception, at.exception
    assert isinstance(at.session_state["selected_artist"], int)
    journey_toggles = [sc for sc in at.segmented_control if sc.options == ["JOURNEY", "ALL LOCATIONS"]]
    assert journey_toggles, "journey/all-locations toggle must appear once an artist is picked"
    body = " ".join(m.value for m in at.markdown)
    assert "One night at random" not in body
