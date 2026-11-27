"""Flask application factory for CQRS Booking."""

import logging
import os
import sqlite3

from flask import Flask, render_template_string, request

from cqrs_booking.availability import QueryService, ReadRegistry, ValidationError

_logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rooms (name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS availability (
    room_name TEXT NOT NULL,
    arrival   TEXT NOT NULL,
    departure TEXT NOT NULL
);
"""

_AVAILABILITY_TEMPLATE = """\
<!doctype html>
<html>
<head><title>Room Availability</title></head>
<body>
  <h1>Search Available Rooms</h1>
  <form method="get" action="/availability">
    <label>Arrival:
      <input type="date" name="arrival"
             value="{{ arrival or '' }}">
    </label>
    <label>Departure:
      <input type="date" name="departure"
             value="{{ departure or '' }}">
    </label>
    <button type="submit">Search</button>
  </form>

  {% if error %}
    <p class="error">{{ error }}</p>
  {% endif %}

  {% if rooms is not none %}
    {% if rooms %}
      <ul>
        {% for room in rooms %}
          <li>{{ room }}</li>
        {% endfor %}
      </ul>
    {% else %}
      <p>No rooms available for the selected dates.</p>
    {% endif %}
  {% endif %}
</body>
</html>
"""


def create_app(query_service: QueryService) -> Flask:
    """Create and return the Flask application.

    *query_service* is injected so tests can supply a mock registry
    without touching SQLite.
    """
    app = Flask(__name__)

    @app.route("/availability")
    def availability():
        arrival = request.args.get("arrival")
        departure = request.args.get("departure")

        rooms = None
        error = None

        if arrival is not None or departure is not None:
            try:
                rooms = query_service.find_available_rooms(arrival, departure)
            except ValidationError as exc:
                error = exc.message
            except Exception:
                # Log component + outcome only; no dates, no SQL internals
                # (AVAILABILITY-INFRA-001.3-S1).
                _logger.error(
                    "availability search failure",
                    exc_info=False,
                )
                error = "Unable to complete the request; please try again."

        return render_template_string(
            _AVAILABILITY_TEMPLATE,
            arrival=arrival,
            departure=departure,
            rooms=rooms,
            error=error,
        )

    return app


def create_app_from_env() -> Flask:
    """Create the application wired to the SQLite database at DATABASE_PATH.

    The schema is created on startup using ``CREATE TABLE IF NOT EXISTS``,
    so existing rooms and reservations on a mounted volume are preserved
    when the container is replaced (AVAILABILITY-INFRA-001.2-S1).
    Configuration is read from the ``DATABASE_PATH`` environment variable
    (default: ``booking.db``).
    """
    db_path = os.environ.get("DATABASE_PATH", "booking.db")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.executescript(_SCHEMA)
    conn.commit()
    registry = ReadRegistry(conn)
    service = QueryService(registry)
    return create_app(query_service=service)
