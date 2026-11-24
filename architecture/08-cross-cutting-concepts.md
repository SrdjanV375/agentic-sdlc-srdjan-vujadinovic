# 8. Cross-cutting Concepts

## Input Validation

- **Availability searches** — Valid arrival and departure dates, with arrival before departure
- **Bookings** — Same date validation, plus non-empty client identifier and existing room (both proposed project rules)

Validation happens before executing the query or booking command.

## Transaction Handling

- **Per-booking transaction** — Each booking attempt uses its own serialized write transaction
- **Overlap check** — Command Service uses WriteRegistry to check authoritative reservations within the transaction, before insertion
- **Atomic update** — Reservation insertion and ReadRegistry update happen within the same transaction
- **Commit after projection** — Commit occurs only after the read projection is updated
- **Rollback on failure** — Any failure triggers rollback of both writes

## Error Handling

- **Booking conflicts** — Display "Room not available for the selected dates"
- **Technical failures** — Display generic "Unable to complete the request; please try again" without internal details

## Logging

- Logs include timestamps, component names, and operation results
- Client identifiers and booking details are excluded from logs
- Only high-level operations (search, booking attempt, success/failure) are logged

## Configuration

- **SQLite database path** — Configurable via environment variable or config file
- Configuration is loaded at application startup

## Authentication

No user authentication or roles are planned. Client identifier is used for booking tracking but is not verified as a secure identity.
