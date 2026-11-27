"""Availability scenarios derived from the approved user stories."""

import sqlite3
from datetime import date
from unittest.mock import MagicMock

import pytest


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


def test_availability_be_001_1_s2_missing_date_rejected_before_query():
    """AVAILABILITY-BE-001.1-S2: Missing arrival rejected before registry query."""
    from cqrs_booking.availability import QueryService, ValidationError

    # GIVEN: The query operation is available; registry is a spy.
    registry = MagicMock()
    service = QueryService(registry)

    # WHEN: A request arrives with a missing arrival date (None).
    with pytest.raises(ValidationError) as exc_info:
        service.find_available_rooms(None, date(2027, 6, 14))

    # THEN: Validation rejects; registry is never called.
    error = exc_info.value
    assert error.field == "arrival"
    assert error.message
    registry.find_available_rooms.assert_not_called()


def test_availability_be_001_1_s2_missing_departure_rejected_before_query():
    """AVAILABILITY-BE-001.1-S2: Missing departure rejected before registry query."""
    from cqrs_booking.availability import QueryService, ValidationError

    # GIVEN: The query operation is available; registry is a spy.
    registry = MagicMock()
    service = QueryService(registry)

    # WHEN: A request arrives with a missing departure date (None).
    with pytest.raises(ValidationError) as exc_info:
        service.find_available_rooms(date(2027, 6, 11), None)

    # THEN: Validation rejects with a departure-field error; registry not called.
    error = exc_info.value
    assert error.field == "departure"
    assert error.message
    registry.find_available_rooms.assert_not_called()


def test_availability_be_001_1_s2_arrival_equal_departure_rejected():
    """AVAILABILITY-BE-001.1-S2: Arrival equal to departure rejected before query."""
    from cqrs_booking.availability import QueryService, ValidationError

    # GIVEN: The query operation is available; registry is a spy.
    registry = MagicMock()
    service = QueryService(registry)

    # WHEN: Arrival and departure are the same date.
    with pytest.raises(ValidationError) as exc_info:
        service.find_available_rooms(date(2027, 6, 15), date(2027, 6, 15))

    # THEN: Validation rejects with an informative message; registry not called.
    error = exc_info.value
    assert error.message
    registry.find_available_rooms.assert_not_called()


def test_availability_be_001_1_s2_arrival_after_departure_rejected():
    """AVAILABILITY-BE-001.1-S2: Arrival after departure rejected before query."""
    from cqrs_booking.availability import QueryService, ValidationError

    # GIVEN: The query operation is available; registry is a spy.
    registry = MagicMock()
    service = QueryService(registry)

    # WHEN: Arrival date is after departure date.
    with pytest.raises(ValidationError) as exc_info:
        service.find_available_rooms(date(2027, 6, 15), date(2027, 6, 12))

    # THEN: Validation rejects with an informative message; registry not called.
    error = exc_info.value
    assert error.message
    registry.find_available_rooms.assert_not_called()
