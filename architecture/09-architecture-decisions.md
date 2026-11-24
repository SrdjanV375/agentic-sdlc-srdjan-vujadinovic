# 9. Architecture Decisions

## ADR-001: Technology Choices for CQRS Booking

### Status

Accepted

### Context

The CQRS Booking kata requires availability searches and room
reservations for one hotel, with separate command and query paths.
The project needs a simple interface and independently testable logic.

### Decision

- Use Python 3.12 and Flask for the application.
- Use HTML templates and CSS for the web interface.
- Use SQLite for persistent room and reservation data.
- Build one modular application with a Command Service, WriteRegistry,
  ReadRegistry and Query Service.
- Update the read projection synchronously within the same transaction
  as the reservation write.
- Use pytest for automated tests and Docker for local execution.
- Keep business logic separate from the web interface.
- Do not introduce event sourcing or microservices.

### Rationale

Python and Flask support a small, understandable application.
SQLite provides persistence without a separate database server.
Separate command and query components satisfy the kata requirements.
Transactional updates keep reservations and availability consistent.
pytest and Docker support the course's testing and CI/CD workflow.

### Consequences

Positive:
- Simple local setup and demonstration.
- Business logic can be tested independently.
- Reservations persist across application restarts.

Negative:
- SQLite limits concurrent write throughput.
- Read-projection consistency requires integration tests.
- Flask and testing dependencies must be maintained.
