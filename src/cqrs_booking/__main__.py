"""Run the CQRS Booking Flask application.

Usage::

    python -m cqrs_booking

Configuration is read from the ``DATABASE_PATH`` environment variable
(default: ``booking.db``).
"""

import os

from cqrs_booking.app import create_app_from_env

app = create_app_from_env()
port = int(os.environ.get("PORT", "5000"))
app.run(host="0.0.0.0", port=port)  # nosec B104
