"""Flask application factory for CQRS Booking."""

from flask import Flask, render_template_string, request

from cqrs_booking.availability import QueryService, ValidationError

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

        return render_template_string(
            _AVAILABILITY_TEMPLATE,
            arrival=arrival,
            departure=departure,
            rooms=rooms,
            error=error,
        )

    return app
