"""Query room availability from the SQLite read projection."""

import sqlite3
from datetime import date


class ValidationError(Exception):
    """Raised when input validation fails.

    Carries a field name and an HTML-suitable message.
    """

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def _parse_date(value, field: str) -> date:
    """Return *value* as a date, or raise ValidationError.

    Accepts an existing ``date`` object unchanged.  Rejects None, empty
    strings, text that cannot be parsed as ISO-8601, and impossible
    calendar dates.
    """
    if value is None:
        raise ValidationError(field, f"{field.capitalize()} date is required.")
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field, f"{field.capitalize()} date is required.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            field,
            f"{field.capitalize()} must be a valid date (YYYY-MM-DD).",
        ) from exc


class ReadRegistry:
    """Read the availability projection without modifying it."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def find_available_rooms(self, arrival: date, departure: date) -> list[str]:
        rows = self.connection.execute(
            """
            SELECT rooms.name
            FROM rooms
            WHERE NOT EXISTS (
                SELECT 1
                FROM availability
                WHERE availability.room_name = rooms.name
                  AND availability.arrival < ?
                  AND availability.departure > ?
            )
            ORDER BY rooms.name
            """,
            (departure.isoformat(), arrival.isoformat()),
        )
        return [row[0] for row in rows]


class QueryService:
    """Handle availability queries using the read registry."""

    def __init__(self, registry: ReadRegistry):
        self.registry = registry

    def find_available_rooms(self, arrival, departure) -> list[str]:
        arrival = _parse_date(arrival, "arrival")
        departure = _parse_date(departure, "departure")
        if arrival >= departure:
            raise ValidationError(
                "arrival",
                "Arrival must be before departure.",
            )
        return self.registry.find_available_rooms(arrival, departure)
