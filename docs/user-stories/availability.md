# Availability — Manual Story Bundle

This bundle is the manual exercise from Module 3, Part 1.
Status: Draft for review. Implementation: Not started.

## AVAILABILITY-STORY-001 — Search available rooms

AS A Hotel User
I WANT to find available rooms for my arrival and departure dates
SO THAT I can choose a room for my stay.

Priority: High. Pareto: Core.

Architecture: [Chapter 1 — Requirements Overview](../../architecture/01-introduction-and-goals.md#requirements-overview),
[Chapter 6 — Search Available Rooms](../../architecture/06-runtime-view.md#search-available-rooms).

### SCENARIO 1: Display available rooms

**Scenario ID**: AVAILABILITY-STORY-001-S1

**GIVEN**
* Rooms A and B exist.
* Room A is reserved from 2027-06-10 to 2027-06-15.
* Room B has no reservations.

**WHEN**
* The Hotel User searches from 2027-06-11 to 2027-06-14.

**THEN**
* The HTML results list contains room B and excludes room A.
* No reservation or availability data is changed.

### SCENARIO 2: No rooms available

**Scenario ID**: AVAILABILITY-STORY-001-S2

**GIVEN**
* Room A is the hotel's only room.
* Room A is reserved from 2027-06-10 to 2027-06-15.

**WHEN**
* The Hotel User searches from 2027-06-11 to 2027-06-14.

**THEN**
* The page clearly states that no rooms are available.
* No room is offered as available.

### SCENARIO 3: Room available starting on departure date

**Scenario ID**: AVAILABILITY-STORY-001-S3

**GIVEN**
* Room A is reserved from 2027-06-10 to 2027-06-15 and has no other reservations.

**WHEN**
* The user searches from 2027-06-15 to 2027-06-18.

**THEN**
* Room A is included in the available results.
* No reservation or availability data is changed.

## AVAILABILITY-FE-001.1 — Search form and results

Parent: AVAILABILITY-STORY-001.

AS A Hotel User
I WANT a date search form with clear results and validation feedback
SO THAT I can find a suitable room or correct my input.

Architecture: [Chapter 3 — Proposed Routes](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes),
[Chapter 10 — Quality Scenarios](../../architecture/10-quality-requirements.md#quality-scenarios).

### SCENARIO 1: Submit a valid search

**Scenario ID**: AVAILABILITY-FE-001.1-S1

**GIVEN**
* The search form is displayed.
* The query response for the selected dates contains only room B.

**WHEN**
* The user enters valid arrival and departure dates and submits the form.

**THEN**
* The HTML results display room B.
* The submitted dates are passed to the query path.

### SCENARIO 2: Explain invalid dates

**Scenario ID**: AVAILABILITY-FE-001.1-S2

**GIVEN**
* The search form is displayed.

**WHEN**
* The user submits arrival 2027-06-14 and departure 2027-06-11.

**THEN**
* The page explains that arrival must be before departure.
* No availability results are presented as valid for that input.

## AVAILABILITY-BE-001.1 — Query availability

Parent: AVAILABILITY-STORY-001.

AS A Hotel User
I WANT availability results to reflect existing reservations
SO THAT I am shown only rooms available for my stay.

Architecture: [Chapter 5 — Components](../../architecture/05-building-block-view.md#components),
[Chapter 8 — Input Validation](../../architecture/08-cross-cutting-concepts.md#input-validation).

### SCENARIO 1: Query the read projection

**Scenario ID**: AVAILABILITY-BE-001.1-S1

**GIVEN**
* ReadRegistry contains rooms A and B.
* A is unavailable from 2027-06-10 to 2027-06-15 and B is available.

**WHEN**
* Query Service receives a search from 2027-06-11 to 2027-06-14.

**THEN**
* The returned room-name set is exactly {B}.
* The operation leaves stored data unchanged.

### SCENARIO 2: Reject invalid dates

**Scenario ID**: AVAILABILITY-BE-001.1-S2

**GIVEN**
* The query operation is available.

**WHEN**
* A request contains a missing or malformed date, or arrival is not before departure.

**THEN**
* Validation rejects the request before the availability query is executed.
* The caller receives a validation result suitable for HTML feedback.

## AVAILABILITY-INFRA-001.1 — Local application deployment

Parent: AVAILABILITY-STORY-001.

AS A developer
I WANT to run the application in a local Docker container
SO THAT the search interface can be demonstrated consistently.

Architecture: [Chapter 7 — Planned Deployment](../../architecture/07-deployment-view.md#planned-deployment-architecture).

### SCENARIO 1: Reach the search interface

**Scenario ID**: AVAILABILITY-INFRA-001.1-S1

**GIVEN**
* The application image is built and its database is initialized.
* The application port is published on the local host.

**WHEN**
* The application container starts and the user opens the search route.

**THEN**
* An HTTP request returns the HTML search form successfully.

## AVAILABILITY-INFRA-001.2 — Persistent availability storage

Parent: AVAILABILITY-STORY-001.

AS A developer
I WANT SQLite data on a persistent Docker volume
SO THAT replacing the application container does not lose availability data.

Architecture: [Chapter 7 — Docker Host](../../architecture/07-deployment-view.md#docker-host),
[Chapter 8 — Configuration](../../architecture/08-cross-cutting-concepts.md#configuration).

### SCENARIO 1: Reuse stored data

**Scenario ID**: AVAILABILITY-INFRA-001.2-S1

**GIVEN**
* The configured SQLite file is on the mounted persistent volume.
* It contains rooms and reservation/projection data for a known search.

**WHEN**
* The application container is replaced using the same volume and configuration.

**THEN**
* The same search returns the same available room names.
* Previously stored reservation and projection data remains intact.

## AVAILABILITY-INFRA-001.3 — Search diagnostics

Parent: AVAILABILITY-STORY-001.

AS A developer
I WANT high-level search outcomes logged
SO THAT I can diagnose failures without exposing booking details.

Architecture: [Chapter 8 — Logging](../../architecture/08-cross-cutting-concepts.md#logging),
[Chapter 8 — Error Handling](../../architecture/08-cross-cutting-concepts.md#error-handling).

### SCENARIO 1: Record a failed search safely

**Scenario ID**: AVAILABILITY-INFRA-001.3-S1

**GIVEN**
* Application logging is enabled.
* The availability data store cannot be read.

**WHEN**
* A valid search is submitted.

**THEN**
* Logs record a timestamp, component and failure outcome.
* Logs exclude client identifiers and booking details.
* The user receives generic failure feedback without database internals.

## Infrastructure Applicability and Dependencies

- Deployment and persistent storage support both search and booking;
  they are shared infrastructure, not separate services per story.
- Monitoring uses the logging approach in Chapter 8.
- Search is read-only and publishes no events.
- No event broker is required. Synchronous projection notification belongs
  to the booking bundle, following Chapters 5 and 6.
- Implementation order: INFRA → BE → FE → original-story E2E verification.

## Date-Boundary Rule

Arrival is inclusive, departure is exclusive. Arrival must be before departure. A new stay may start on the previous stay's departure date (see [Chapter 11](../../architecture/11-risks-and-technical-debts.md)).

## Traceability

| Scenario ID | Containing Story ID | Architecture reference |
|-------------|---------------------|------------------------|
| AVAILABILITY-STORY-001-S1 | AVAILABILITY-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 6](../../architecture/06-runtime-view.md#search-available-rooms) |
| AVAILABILITY-STORY-001-S2 | AVAILABILITY-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 6](../../architecture/06-runtime-view.md#search-available-rooms) |
| AVAILABILITY-STORY-001-S3 | AVAILABILITY-STORY-001 | [Chapter 1](../../architecture/01-introduction-and-goals.md#requirements-overview), [Chapter 6](../../architecture/06-runtime-view.md#search-available-rooms), [Chapter 11](../../architecture/11-risks-and-technical-debts.md) |
| AVAILABILITY-FE-001.1-S1 | AVAILABILITY-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 10](../../architecture/10-quality-requirements.md#quality-scenarios) |
| AVAILABILITY-FE-001.1-S2 | AVAILABILITY-FE-001.1 | [Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes), [Chapter 10](../../architecture/10-quality-requirements.md#quality-scenarios) |
| AVAILABILITY-BE-001.1-S1 | AVAILABILITY-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| AVAILABILITY-BE-001.1-S2 | AVAILABILITY-BE-001.1 | [Chapter 5](../../architecture/05-building-block-view.md#components), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#input-validation) |
| AVAILABILITY-INFRA-001.1-S1 | AVAILABILITY-INFRA-001.1 | [Chapter 7](../../architecture/07-deployment-view.md#planned-deployment-architecture) |
| AVAILABILITY-INFRA-001.2-S1 | AVAILABILITY-INFRA-001.2 | [Chapter 7](../../architecture/07-deployment-view.md#docker-host), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#configuration) |
| AVAILABILITY-INFRA-001.3-S1 | AVAILABILITY-INFRA-001.3 | [Chapter 8](../../architecture/08-cross-cutting-concepts.md#logging), [Chapter 8](../../architecture/08-cross-cutting-concepts.md#error-handling) |
