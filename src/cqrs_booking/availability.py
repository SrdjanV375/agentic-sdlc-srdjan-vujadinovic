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

    def find_available_rooms(self, arrival: date, departure: date) -> list[str]:
        if arrival is None:
            raise ValidationError("arrival", "Arrival date is required.")
        return self.registry.find_available_rooms(arrival, departure)
