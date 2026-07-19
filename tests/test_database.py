import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'data' / 'concerts.sqlite'


def test_database_counts():
    with sqlite3.connect(DB) as c:
        assert c.execute('select count(*) from events').fetchone()[0] == 654
        assert c.execute('select count(*) from artists').fetchone()[0] > 900
        assert c.execute('select count(*) from event_artists').fetchone()[0] > 1700


def test_no_orphan_event_artists():
    with sqlite3.connect(DB) as c:
        n = c.execute('select count(*) from event_artists ea left join events e on e.event_id=ea.event_id where e.event_id is null').fetchone()[0]
        assert n == 0


def test_reviewed_aliases_are_applied():
    """Only the approved alias table merges variants; originals stay in original_text."""
    with sqlite3.connect(DB) as c:
        gone = c.execute("select count(*) from artists where display_name in "
                         "('Toad the Wet Sprockett','Five For Fightning','Tom Petty & the Heartbrakers')").fetchone()[0]
        assert gone == 0
        kept = c.execute("select count(*) from event_artists where original_text like 'Toad the Wet Sprocket%'").fetchone()[0]
        assert kept >= 1
        # Festival years must never be merged.
        ol = c.execute("select count(*) from artists where display_name like 'Outside Lands 20%'").fetchone()[0]
        assert ol >= 4


def test_no_fabricated_coordinates():
    """Any stored coordinate must carry a geocode status explaining its source."""
    with sqlite3.connect(DB) as c:
        for table in ("cities", "venues"):
            n = c.execute(f"select count(*) from {table} where latitude is not null "
                          f"and (geocode_status is null or geocode_status='unresolved')").fetchone()[0]
            assert n == 0
