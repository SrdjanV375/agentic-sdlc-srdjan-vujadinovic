# 10. Quality Requirements

## Quality Tree

```
Quality Requirements
├── Correctness
│   └── Overlapping reservations are prevented
├── Consistency
│   ├── Availability reflects successful bookings
│   └── Failed transactions leave no partial changes
├── Persistence
│   └── Reservations survive application-container replacement
├── Usability
│   ├── Clear search results
│   ├── Clear booking feedback
│   └── Validation feedback
└── Testability
    └── Command/query business logic testable without Flask or HTTP
```

## Quality Scenarios

Verification targets—not tests already implemented or passed:

| Trigger | Expected Response | Pass Condition |
|---------|-------------------|----------------|
| Two concurrent requests attempt to book the same room for overlapping dates | Only one booking succeeds; the other is rejected | At most one reservation exists for any room/date overlap |
| Booking request is valid and room is available | Reservation is created; availability is updated; success page is shown | ReadRegistry shows room unavailable for the booked period |
| Booking request conflicts with existing reservation | Booking is rejected with "Room not available" message | No new reservation is created; availability unchanged |
| Application-container replacement using the same persistent volume | Previously committed reservations and availability remain unchanged | After replacing the application container and reusing the same volume, previously committed reservations and availability remain unchanged |
| User searches availability with valid dates | HTML page lists exactly the available rooms from prepared test data, or a clear empty result | All and only available rooms are displayed |
| Booking request has invalid dates (departure before arrival) | Validation error shown; no booking attempt | Error message displayed for each invalid field |
| Booking request references non-existent room | Validation error shown; no booking attempt | Error message indicates room not found |
| Read-projection update fails after reservation insertion | Transaction rolls back; neither reservation nor projection change is committed | No reservation created; availability unchanged |
| Command/query business logic is invoked programmatically | Tests run without starting Flask or making HTTP requests | All domain functions pass unit tests; mocks optional |
