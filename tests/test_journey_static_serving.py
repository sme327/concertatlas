"""The journey player's map only renders when served as a real navigated URL.

Regression coverage for a confirmed bug: the vendored MapLibre build never
loads any vector tiles when its document's location is the special
"about:srcdoc" value (which is how Streamlit's st.iframe embeds a raw HTML
string) — markers still animate since they're plain DOM elements, but the
basemap stays black forever. Verified directly: a plain fetch() to the same
tile URL succeeds from a srcdoc context, and the identical style loads in
under a second once served from a real file instead. Confirmed via a real
Playwright/Chromium session, not just DOM/state inspection.

Fix: render_journey_player writes the player HTML into static/ and points
st.iframe at that URL, which requires enableStaticServing = true.
"""
import tomllib
from pathlib import Path

from src.components.journey import STATIC_DIR, _write_static_html, render_journey_player


def test_static_serving_enabled_in_config():
    config_path = Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml"
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    assert config.get("server", {}).get("enableStaticServing") is True, (
        "the journey map goes permanently black without this — see journey.py's module docstring"
    )


def test_write_static_html_reuses_file_for_identical_content(tmp_path, monkeypatch):
    monkeypatch.setattr("src.components.journey.STATIC_DIR", tmp_path)
    url1 = _write_static_html("<html>same content</html>")
    mtime1 = (tmp_path / url1.split("/")[-1]).stat().st_mtime
    url2 = _write_static_html("<html>same content</html>")
    assert url1 == url2
    assert (tmp_path / url2.split("/")[-1]).stat().st_mtime == mtime1  # not rewritten


def test_write_static_html_never_collides_across_different_journeys(tmp_path, monkeypatch):
    monkeypatch.setattr("src.components.journey.STATIC_DIR", tmp_path)
    url_a = _write_static_html("<html>artist A's journey</html>")
    url_b = _write_static_html("<html>artist B's journey</html>")
    assert url_a != url_b
    assert (tmp_path / url_a.split("/")[-1]).read_text() == "<html>artist A's journey</html>"
    assert (tmp_path / url_b.split("/")[-1]).read_text() == "<html>artist B's journey</html>"


def test_static_url_is_never_inline_html():
    """render_journey_player must hand st.iframe a URL path, not raw markup —
    passing raw HTML re-introduces the srcdoc bug this file guards against."""
    import streamlit as st

    calls = []
    original = st.iframe
    st.iframe = lambda src, **kw: calls.append(src)
    try:
        render_journey_player([], "Test", "Test", height=400)
    finally:
        st.iframe = original
    assert len(calls) == 1
    assert calls[0].startswith("/app/static/") and calls[0].endswith(".html")
    assert "<html" not in calls[0].lower()
