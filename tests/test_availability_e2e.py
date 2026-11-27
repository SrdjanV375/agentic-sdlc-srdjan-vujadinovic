"""E2E scenarios for AVAILABILITY-STORY-001 through the Flask test client."""

import sqlite3

import pytest

_SCHEMA = """
CREATE TABLE rooms (name TEXT PRIMARY KEY);
CREATE TABLE availability (
    room_name TEXT NOT NULL,
    arrival   TEXT NOT NULL,
    departure TEXT NOT NULL
);
"""


def _make_client(connection):
    """Return a Flask test client wired to *connection*."""
    from cqrs_booking.app import create_app
    from cqrs_booking.availability import QueryService, ReadRegistry

    registry = ReadRegistry(connection)
    service = QueryService(registry)
    app = create_app(query_service=service)
    return app.test_client()


@pytest.fixture()
def db():
    """Yield an in-memory SQLite connection with the schema created."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# AVAILABILITY-STORY-001-S1
# ---------------------------------------------------------------------------


def test_availability_story_001_s1_reserved_a_search_returns_only_b(db):
    """AVAILABILITY-STORY-001-S1: HTML results list B, exclude A."""
    # GIVEN: Rooms A and B exist; A is reserved 2027-06-10 to 2027-06-15.
    db.executescript(
        """
        INSERT INTO rooms (name) VALUES ('A'), ('B');
        INSERT INTO availability (room_name, arrival, departure)
        VALUES ('A', '2027-06-10', '2027-06-15');
        """
    )
    client = _make_client(db)

    rooms_before = db.execute("SELECT * FROM rooms ORDER BY name").fetchall()
    availability_before = db.execute(
        "SELECT * FROM availability ORDER BY room_name, arrival"
    ).fetchall()
    changes_before = db.total_changes

    # WHEN: Hotel User searches from 2027-06-11 to 2027-06-14.
    response = client.get(
        "/availability",
        query_string={"arrival": "2027-06-11", "departure": "2027-06-14"},
    )

    # THEN: HTML results contain B and exclude A; no data is changed.
    assert response.status_code == 200
    body = response.data.decode()
    assert "<li>B</li>" in body
    assert "<li>A</li>" not in body

    assert db.execute("SELECT * FROM rooms ORDER BY name").fetchall() == rooms_before
    assert (
        db.execute("SELECT * FROM availability ORDER BY room_name, arrival").fetchall()
        == availability_before
    )
    assert db.total_changes == changes_before


# ---------------------------------------------------------------------------
# AVAILABILITY-STORY-001-S2
# ---------------------------------------------------------------------------


def test_availability_story_001_s2_no_rooms_available_message(db):
    """AVAILABILITY-STORY-001-S2: Page states no rooms available."""
    # GIVEN: Room A is the hotel's only room; it is reserved 2027-06-10 to 2027-06-15.
    db.executescript(
        """
        INSERT INTO rooms (name) VALUES ('A');
        INSERT INTO availability (room_name, arrival, departure)
        VALUES ('A', '2027-06-10', '2027-06-15');
        """
    )
    client = _make_client(db)

    rooms_before = db.execute("SELECT * FROM rooms ORDER BY name").fetchall()
    availability_before = db.execute(
        "SELECT * FROM availability ORDER BY room_name, arrival"
    ).fetchall()
    changes_before = db.total_changes

    # WHEN: Hotel User searches from 2027-06-11 to 2027-06-14.
    response = client.get(
        "/availability",
        query_string={"arrival": "2027-06-11", "departure": "2027-06-14"},
    )

    # THEN: Page clearly states no rooms are available; no room is offered.
    assert response.status_code == 200
    body = response.data.decode()
    assert "No rooms available" in body
    assert "<li>" not in body

    assert db.execute("SELECT * FROM rooms ORDER BY name").fetchall() == rooms_before
    assert (
        db.execute("SELECT * FROM availability ORDER BY room_name, arrival").fetchall()
        == availability_before
    )
    assert db.total_changes == changes_before
