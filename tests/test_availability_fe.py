"""FE scenarios for availability — search form and results."""

from datetime import date
from unittest.mock import MagicMock


def test_availability_fe_001_1_s1_valid_search_displays_room():
    """AVAILABILITY-FE-001.1-S1: Valid search displays the available room."""
    from cqrs_booking.app import create_app
    from cqrs_booking.availability import QueryService

    # GIVEN: The search form is displayed; query response for the dates contains B.
    registry = MagicMock()
    registry.find_available_rooms.return_value = ["B"]
    service = QueryService(registry)
    app = create_app(query_service=service)
    client = app.test_client()

    # WHEN: GET /availability is requested without parameters.
    empty_response = client.get("/availability")

    # THEN: The form is present, targeting /availability with GET,
    # with date inputs named arrival and departure; registry is not called.
    assert empty_response.status_code == 200
    empty_body = empty_response.data.decode()
    assert 'method="get"' in empty_body
    assert 'action="/availability"' in empty_body
    assert 'name="arrival"' in empty_body
    assert 'name="departure"' in empty_body
    registry.find_available_rooms.assert_not_called()

    # WHEN: The user submits valid arrival and departure dates.
    response = client.get(
        "/availability",
        query_string={"arrival": "2027-06-11", "departure": "2027-06-14"},
    )

    # THEN: HTTP 200 is returned, B appears as a list item in the results,
    # and the registry was called exactly once with the parsed date objects.
    assert response.status_code == 200
    body = response.data.decode()
    assert "<li>B</li>" in body
    registry.find_available_rooms.assert_called_once_with(
        date(2027, 6, 11),
        date(2027, 6, 14),
    )
