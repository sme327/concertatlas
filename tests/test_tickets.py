from types import SimpleNamespace

import pandas as pd
import pytest

from src.ui import also_listed, ticket_html

ROW = SimpleNamespace(
    event_id=17,
    event_date=pd.Timestamp("2026-12-05"),
    event_title="Counting Crows",
    venue="Metro",
    city="Chicago",
    state_region="Illinois",
    is_upcoming=1,
)


@pytest.mark.parametrize("variant", ["upcoming_full", "past_torn", "journey_compact"])
def test_no_fabricated_ticket_fields(variant):
    """Tickets must never manufacture seat/section/row/price/gate data."""
    html = ticket_html(ROW, ["Counting Crows", "Live"], variant).upper()
    for forbidden in ("SEAT", "SECTION", "ROW ", "GATE", "PRICE", "$"):
        assert forbidden not in html, f"{variant} fabricates {forbidden!r}"


def test_upcoming_full_has_stub_stamp_and_archive_number():
    html = ticket_html(ROW, [], "upcoming_full")
    assert "UPCOMING" in html and "ADMIT ONE" in html
    assert "№ 000017" in html  # decorative number derived from real event id


def test_past_torn_has_no_stub():
    past = SimpleNamespace(**{**ROW.__dict__, "is_upcoming": 0})
    html = ticket_html(past, [], "past_torn")
    assert "torn" in html and "ADMIT ONE" not in html and "UPCOMING" not in html


def test_real_fields_render():
    html = ticket_html(ROW, ["Counting Crows", "Live"], "past_torn")
    for needle in ("DEC", "05", "2026", "Counting Crows", "Metro", "Chicago"):
        assert needle in html


def test_year_leads_the_date_block():
    html = ticket_html(ROW, [], "past_torn")
    assert html.index('d-year') < html.index('d-md'), "year must be the dominant date element"


def test_past_ticket_marked_archived_upcoming_not():
    past = SimpleNamespace(**{**ROW.__dict__, "is_upcoming": 0})
    assert "ARCHIVED" in ticket_html(past, [], "past_torn")
    assert "ARCHIVED" not in ticket_html(ROW, [], "upcoming_full")


def test_meta_line_renders_only_when_supplied():
    assert "TIME #12" in ticket_html(ROW, [], "journey_compact", meta="TIME #12")
    assert "tk-meta" not in ticket_html(ROW, [], "journey_compact")


def test_duplicate_artist_shown_only_once():
    # Bill repeats the event title -> the name appears once, no ALSO LISTED line.
    html = ticket_html(ROW, ["Counting Crows"], "past_torn")
    assert html.count("Counting Crows") == 1
    assert "ALSO LISTED" not in html


def test_additional_artists_get_labeled_line():
    html = ticket_html(ROW, ["Counting Crows", "The Wallflowers"], "past_torn")
    assert "ALSO LISTED:" in html and "The Wallflowers" in html
    assert html.count("Counting Crows") == 1


def test_also_listed_helper():
    assert also_listed("Counting Crows", ["Counting Crows", "Live"]) == ["Live"]
    assert also_listed("Counting Crows", ["Counting Crows"]) == []
    assert also_listed("Lollapalooza '10", ["Green Day", "Soundgarden"]) == ["Green Day", "Soundgarden"]


def test_square_corner_physicality():
    # No rounded-card silhouette: tickets carry the paper classes, not a big radius.
    html = ticket_html(ROW, [], "upcoming_full")
    assert 'class="ticket full"' in html and "tk-perf" in html and "ADMIT ONE" in html
