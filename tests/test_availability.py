"""Availability scenarios derived from the approved user stories."""

import sqlite3
from datetime import date


def test_availability_be_001_1_s1_given_reserved_a_when_search_then_only_b():
    """AVAILABILITY-BE-001.1-S1: Query the read projection."""
    from cqrs_booking.availability import QueryService, ReadRegistry

    connection = sqlite3.connect(":memory:")
    try:
        # GIVEN: ReadRegistry contains A and B; A is unavailable June 10–15.
        connection.executescript(
            """
            CREATE TABLE rooms (name TEXT PRIMARY KEY);
            CREATE TABLE availability (
                room_name TEXT NOT NULL,
                arrival TEXT NOT NULL,
                departure TEXT NOT NULL
            );
            INSERT INTO rooms (name) VALUES ('A'), ('B');
            INSERT INTO availability (room_name, arrival, departure)
            VALUES ('A', '2027-06-10', '2027-06-15');
            """
        )
        registry = ReadRegistry(connection)
        service = QueryService(registry)
        data_before = tuple(connection.iterdump())
        changes_before = connection.total_changes

        # WHEN: Search for a stay from June 11 to June 14.
        available_rooms = service.find_available_rooms(
            date(2027, 6, 11),
            date(2027, 6, 14),
        )

        # THEN: Only B is returned, and stored data remains unchanged.
        assert set(available_rooms) == {"B"}
        assert tuple(connection.iterdump()) == data_before
        assert connection.total_changes == changes_before
    finally:
        connection.close()
