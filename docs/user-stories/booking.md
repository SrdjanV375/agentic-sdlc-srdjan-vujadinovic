# Booking — Agent-Generated Story Bundle

This bundle is the agent-generated exercise from Module 3, Part 2.
Status: Approved for documentation. Implementation: Not started.

## BOOKING-STORY-001 — Reserve a room

AS A Hotel User
I WANT to reserve an available room using my client identifier and stay dates
SO THAT the room is reserved for my stay.

Priority: High. Pareto: Core.

Architecture: [Chapter 1 — Requirements Overview](../../architecture/01-introduction-and-goals.md#requirements-overview),
[Chapter 5 — Components](../../architecture/05-building-block-view.md#components),
[Chapter 6 — Successful Booking](../../architecture/06-runtime-view.md#successful-booking),
[Chapter 6 — Reject Overlapping Booking](../../architecture/06-runtime-view.md#reject-overlapping-booking),
[Chapter 11 — Risks and Technical Debts](../../architecture/11-risks-and-technical-debts.md).

### SCENARIO 1: Successful booking

**Scenario ID**: BOOKING-STORY-001-S1

**GIVEN**
* Room A is available for the requested dates (2027-06-20 to 2027-06-25).
* The client identifier is "C123".
* The date-boundary rule applies: arrival is inclusive, departure is exclusive; a new stay may start on the previous stay's departure date.

**WHEN**
* The Hotel User submits a booking request for Room A with dates 2027-06-20 to 2027-06-25.

**THEN**
* A reservation is created for Room A, client C123, 2027-06-20 to 2027-06-25.
* The availability read projection is updated to reflect the reservation.
* The Web Interface displays a booking confirmation.

### SCENARIO 2: Overlapping booking rejected

**Scenario ID**: BOOKING-STORY-001-S2

**GIVEN**
* Room A is reserved from 2027-06-10 to 2027-06-15.
* The client identifier is "C456".

**WHEN**
* The Hotel User submits a booking request for Room A with dates 2027-06-12 to 2027-06-17.

**THEN**
* The booking is rejected with "Room not available for the selected dates".
* No reservation is created.
* The reservation and availability read projection remain unchanged.

### SCENARIO 3: Booking starting on previous departure date

**Scenario ID**: BOOKING-STORY-001-S3

**GIVEN**
* Room A is reserved from 2027-06-10 to 2027-06-15 and has no other conflicting reservations.
* The client identifier is "C789".

**WHEN**
* The Hotel User submits a booking request for Room A with dates 2027-06-15 to 2027-06-18.

**THEN**
* A reservation is created for Room A, client C789, 2027-06-15 to 2027-06-18.
* The availability read projection is updated.
* The Web Interface displays a booking confirmation.

### SCENARIO 4: Invalid dates rejected

**Scenario ID**: BOOKING-STORY-001-S4

**GIVEN**
* The client identifier is "C123".

**WHEN**
* The user submits arrival 2027-06-15 and departure 2027-06-12.

**THEN**
* The page explains that arrival must be before departure.
* No reservation is created.
* No reservation or availability data is changed.

### SCENARIO 5: Non-existent room rejected

**Scenario ID**: BOOKING-STORY-001-S5

**GIVEN**
* The client identifier is "C123".

**WHEN**
* The user submits a booking request for a room that does not exist.

**THEN**
* The page explains that the room was not found.
* No reservation is created.
* No reservation or availability data is changed.

### SCENARIO 6: Empty client identifier rejected

**Scenario ID**: BOOKING-STORY-001-S6

**GIVEN**
* The user prepares a booking request.

**WHEN**
* The user submits a booking request with an empty client identifier.

**THEN**
* The page explains that the client identifier is required.
* No reservation is created.
* No reservation or availability data is changed.

## BOOKING-FE-001.1 — Booking form and results

Parent: BOOKING-STORY-001.

AS A Hotel User
I WANT a booking form with validation feedback and clear outcomes
SO THAT I can submit a valid reservation or correct my input.

Architecture: [Chapter 3 — Proposed Routes](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes),
[Chapter 8 — Input Validation](../../architecture/08-cross-cutting-concepts.md#input-validation),
[Chapter 8 — Error Handling](../../architecture/08-cross-cutting-concepts.md#error-handling).

### SCENARIO 1: Valid booking submission

**Scenario ID**: BOOKING-FE-001.1-S1

**GIVEN**
* The booking form is displayed.
* All inputs (client identifier, room, dates) are valid.

**WHEN**
* The user submits the booking form.

**THEN**
* The form data is sent to the `/book` POST endpoint.
* A booking confirmation page is displayed on success.

### SCENARIO 2: Invalid date feedback

**Scenario ID**: BOOKING-FE-001.1-S2

**GIVEN**
* The booking form is displayed.

**WHEN**
* The user submits arrival 2027-06-17 and departure 2027-06-15.

**THEN**
* The page shows an error for the date fields.
* No reservation is created.
* No availability data is changed.

### SCENARIO 3: Unknown room feedback

**Scenario ID**: BOOKING-FE-001.1-S3

**GIVEN**
* The booking form is displayed.

**WHEN**
* The user submits a booking request for an unknown room name.

**THEN**
* The page shows an error indicating the room was not found.
* No reservation is created.
* No availability data is changed.

### SCENARIO 4: Empty client identifier feedback

**Scenario ID**: BOOKING-FE-001.1-S4

**GIVEN**
* The booking form is displayed.

**WHEN**
* The user submits with an empty client identifier field.

**THEN**
* The page shows an error indicating the client identifier is required.
* No reservation is created.
* No availability data is changed.

## BOOKING-BE-001.1 — Process booking command

Parent: BOOKING-STORY-001.

AS A Hotel User
I WANT bookings to validate inputs, check overlaps, and update availability atomically
SO THAT I am not double-booked and availability is accurate.

Architecture: [Chapter 5 — Components](../../architecture/05-building-block-view.md#components),
[Chapter 6 — Transaction Handling](../../architecture/06-runtime-view.md#successful-booking),
[Chapter 8 — Input Validation](../../architecture/08-cross-cutting-concepts.md#input-validation),
[Chapter 8 — Transaction Handling](../../architecture/08-cross-cutting-concepts.md#transaction-handling).

### SCENARIO 1: Successful booking with atomic update

**Scenario ID**: BOOKING-BE-001.1-S1

**GIVEN**
* WriteRegistry contains no conflicting reservation for the requested room/dates.
* ReadRegistry contains the current availability projection.

**WHEN**
* Command Service receives a valid booking request.

**THEN**
* A serialized write transaction begins before checking authoritative reservations in WriteRegistry.
* The overlap check, reservation insertion and synchronous ReadRegistry update all occur within that same transaction.
* The transaction commits successfully.
* Success is returned only after commit.

### SCENARIO 2: Overlapping booking rejected with rollback

**Scenario ID**: BOOKING-BE-001.1-S2

**GIVEN**
* WriteRegistry contains a reservation that overlaps with the requested dates.

**WHEN**
* Command Service initiates a serialized write transaction and performs authoritative overlap checking.

**THEN**
* The overlap is detected.
* The transaction is rolled back.
* Command Service returns "Room not available for the selected dates".
* No reservation is created; ReadRegistry remains unchanged.

### SCENARIO 3: Read-projection update failure triggers rollback

**Scenario ID**: BOOKING-BE-001.1-S3

**GIVEN**
* WriteRegistry is configured to fail on the ReadRegistry update step.
* WriteRegistry contains no conflicting reservation for the requested room/dates.
* ReadRegistry is available but will fail during update.

**WHEN**
* Command Service receives a valid booking request.

**THEN**
* The transaction is rolled back.
* No reservation is created in WriteRegistry.
* ReadRegistry remains unchanged.
* Command Service returns a generic failure (no success confirmation).

### SCENARIO 4: Validation failure before transaction

**Scenario ID**: BOOKING-BE-001.1-S4

**GIVEN**
* Command Service receives a request with invalid dates or an unknown room name.

**WHEN**
* Input validation is performed.

**THEN**
* Validation rejects the request before any transaction is started.
* No reservation or projection data is changed.
* The caller receives a validation result suitable for HTML feedback.

### SCENARIO 5: Empty client identifier validation

**Scenario ID**: BOOKING-BE-001.1-S5

**GIVEN**
* Command Service receives a request with an empty client identifier.

**WHEN**
* Input validation is performed.

**THEN**
* Validation rejects the request before any transaction is started.
* No reservation or projection data is changed.
* The caller receives a validation result suitable for HTML feedback.

## BOOKING-INFRA-001.1 — Local application deployment

Parent: BOOKING-STORY-001.

AS A developer
I WANT to run the application in a local Docker container
SO THAT the booking interface can be demonstrated consistently.

Architecture: [Chapter 7 — Planned Deployment](../../architecture/07-deployment-view.md#planned-deployment-architecture),
[AVAILABILITY-INFRA-001.1](./availability.md).

### SCENARIO 1: Reach the booking interface

**Scenario ID**: BOOKING-INFRA-001.1-S1

**GIVEN**
* The application image is built and its database is initialized.
* The application port is published on the local host.
* Existing rooms are seeded in the database.

**WHEN**
* The application container starts and the user navigates to the booking route.

**THEN**
* An HTTP request returns the HTML booking form successfully.

### SCENARIO 2: Booking via Docker container

**Scenario ID**: BOOKING-INFRA-001.1-S2

**GIVEN**
* The application container is running with the persistent volume mounted.
* A valid room exists in the seeded data.

**WHEN**
* A booking request is submitted via the web interface.

**THEN**
* The booking is processed and persisted.
* A booking confirmation is displayed.

## BOOKING-INFRA-001.2 — Persistent booking storage

Parent: BOOKING-STORY-001.

AS A developer
I WANT SQLite data on a persistent Docker volume
SO THAT replacing the application container does not lose booking data.

Architecture: [Chapter 7 — Docker Host](../../architecture/07-deployment-view.md#docker-host),
[Chapter 8 — Configuration](../../architecture/08-cross-cutting-concepts.md#configuration),
[AVAILABILITY-INFRA-001.2](./availability.md).

### SCENARIO 1: Reuse stored reservations

**Scenario ID**: BOOKING-INFRA-001.2-S1

**GIVEN**
* The configured SQLite file is on the mounted persistent volume.
* It contains bookings and the availability projection for a known room.

**WHEN**
* The application container is replaced using the same volume and configuration.

**THEN**
* The same room shows the same reservation status.
* Previously committed reservations and projection data remain intact.

## BOOKING-INFRA-001.3 — Booking diagnostics

Parent: BOOKING-STORY-001.

AS A developer
I WANT high-level booking outcomes logged without exposing client identifiers or booking details
SO THAT I can diagnose failures while protecting user privacy.

Architecture: [Chapter 8 — Logging](../../architecture/08-cross-cutting-concepts.md#logging),
[Chapter 8 — Error Handling](../../architecture/08-cross-cutting-concepts.md#error-handling),
[AVAILABILITY-INFRA-001.3](./availability.md).

### SCENARIO 1: Record a successful booking safely

**Scenario ID**: BOOKING-INFRA-001.3-S1

**GIVEN**
* Application logging is enabled.
* A valid booking request is processed.

**WHEN**
* The booking completes successfully.

**THEN**
* Logs record a timestamp, component, and "success" outcome.
* Logs exclude client identifiers and booking details.

### SCENARIO 2: Record a failed booking safely

**Scenario ID**: BOOKING-INFRA-001.3-S2

**GIVEN**
* Application logging is enabled.
* The booking fails due to overlap or validation.

**WHEN**
* The booking is rejected.

**THEN**
* Logs record a timestamp, component, and "failure" outcome.
* Logs exclude client identifiers and booking details.
* The user receives appropriate specific feedback.

## Infrastructure Applicability and Dependencies

- Deployment (INFRA-001.1) and persistent storage (INFRA-001.2) are shared with availability (see AVAILABILITY-INFRA-001.1 and AVAILABILITY-INFRA-001.2);
  they support both search and booking, not separate services per story.
- Monitoring uses the logging approach in Chapter 8 for both search and booking (see AVAILABILITY-INFRA-001.3).
- No event broker is required. Synchronous projection notification occurs within the booking transaction.
- Booking must not require a prior availability search; it validates availability against authoritative WriteRegistry data.
- Implementation order: INFRA → BE → FE → original-story E2E verification.

## Traceability

| Scenario ID | Containing Story ID | Architecture reference |
|-------------|---------------------|------------------------|
| BOOKING-STORY-001-S1 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#successful-booking), [Chapter 11](../../architecture/11-risks-and-technical-debts.md) |
| BOOKING-STORY-001-S2 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#reject-overlapping-booking), [Chapter 11](../../architecture/11-risks-and-technical-debts.md) |
| BOOKING-STORY-001-S3 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#successful-booking), [Chapter 11](../../architecture/11-risks-and-technical-debts.md) |
| BOOKING-STORY-001-S4 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-STORY-001-S5 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-STORY-001-S6 | BOOKING-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-FE-001.1-S1 | BOOKING-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#error-handling) |
| BOOKING-FE-001.1-S2 | BOOKING-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-FE-001.1-S3 | BOOKING-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-FE-001.1-S4 | BOOKING-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-BE-001.1-S1 | BOOKING-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#successful-booking), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#transaction-handling) |
| BOOKING-BE-001.1-S2 | BOOKING-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#reject-overlapping-booking), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#transaction-handling) |
| BOOKING-BE-001.1-S3 | BOOKING-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 6](../../architecture/06-runtime-view.md#successful-booking), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#transaction-handling) |
| BOOKING-BE-001.1-S4 | BOOKING-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-BE-001.1-S5 | BOOKING-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| BOOKING-INFRA-001.1-S1 | BOOKING-INFRA-001.1 | [Chapter 7](../../architecture/07-deployment-view.md#planned-deployment-architecture), [AVAILABILITY-INFRA-001.1](./availability.md) |
| BOOKING-INFRA-001.1-S2 | BOOKING-INFRA-001.1 | [Chapter 7](../../architecture/07-deployment-view.md#docker-host), [Chapter 7](../../architecture/07-deployment-view.md#planned-deployment-architecture) |
| BOOKING-INFRA-001.2-S1 | BOOKING-INFRA-001.2 | [Chapter 7](../../architecture/07-deployment-view.md#docker-host), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#configuration), [AVAILABILITY-INFRA-001.2](./availability.md) |
| BOOKING-INFRA-001.3-S1 | BOOKING-INFRA-001.3 | [Chapter 8](../../architecture/08-cross-cutting-concepts.md#logging), [AVAILABILITY-INFRA-001.3](./availability.md) |
| BOOKING-INFRA-001.3-S2 | BOOKING-INFRA-001.3 | [Chapter 8](../../architecture/08-cross-cutting-concepts.md#logging), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#error-handling), [AVAILABILITY-INFRA-001.3](./availability.md) |
