"""Lightweight boot checks: every page must run without raising."""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["app.py", "pages/1_Artists.py", "pages/2_Shows.py", "pages/3_About_the_Data.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_boots(page):
    at = AppTest.from_file(page, default_timeout=30)
    at.run()
    assert not at.exception, f"{page} raised: {at.exception}"
