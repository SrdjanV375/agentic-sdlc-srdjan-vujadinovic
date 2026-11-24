# 4. Solution Strategy

## Architectural Pattern

The system follows a CQRS pattern with separate command/write and query/read paths:
- **Command side**: Web interface accepts booking requests; Command Service coordinates with WriteRegistry to create reservations
- **Query side**: Query Service retrieves availability from ReadRegistry for search results
- **Consistency**: ReadRegistry is updated synchronously within the booking transaction to maintain availability consistency

## Technology Strategy

- **Flask with server-rendered HTML** — Simple, understandable application structure; no client-side JavaScript framework required
- **SQLite** — Single-file database for reservations and availability; no separate database server needed
- **pytest** — Unit and integration testing aligned with TDD practices from Module 5
- **Docker** — Local development (serves HTTP) and CI/CD execution (pytest, then exits) per Module 4 requirements

## Quality Goal Support

- **Correctness** — Before inserting a reservation, the Command Service checks for overlapping reservations against authoritative data in WriteRegistry. This check and insertion occur within a serialized write transaction, preventing concurrent requests from reserving the same room and period. ReadRegistry is updated in that same transaction. If any step fails, both writes roll back. Synchronous projection updates keep search results consistent; they do not by themselves prevent double booking.
- **Simplicity** — One modular application with clear component separation; server-rendered HTML keeps the stack straightforward
- **Testability** — Business logic separated from Flask presentation layer; pytest supports isolated component testing
- **Maintainability** — Clear CQRS boundaries between command and query responsibilities
- **Local development** — Docker container runs the Flask app for local use; the CI test command runs pytest and exits

## Component Responsibilities (proposed)

| Component | Responsibility |
|-----------|----------------|
| Web Interface | Renders HTML forms and pages, routes HTTP requests |
| Command Service | Processes booking commands, validates inputs, performs overlap checks |
| WriteRegistry | Stores authoritative reservations in SQLite |
| ReadRegistry | Maintains availability read projection |
| Query Service | Finds available rooms for date ranges |
