# 12. Glossary

| Term | Meaning in this project |
|------|-------------------------|
| CQRS | Command Query Responsibility Segregation; separate command and query paths for reservations and availability searches |
| Command Service | Coordinates booking validation, overlap checking and reservation writes through WriteRegistry |
| Query Service | Component that finds available rooms by querying the read projection |
| WriteRegistry | Component storing authoritative reservations in SQLite; handles overlap checks and writes |
| ReadRegistry | Component maintaining the availability read projection; updated synchronously within the booking transaction |
| Read projection | Denormalized availability data derived from authoritative reservations |
| Authoritative reservations | The source-of-truth reservation records stored in SQLite and accessed through WriteRegistry |
| Booking | Reservation of a room for a client identifier for a specific arrival-to-departure period |
| Client identifier | Guest-provided string for reservation tracking; not a verified identity |
| Transaction | A group of database operations committed or rolled back together; booking write transactions are serialized |
| Commit | Finalize a transaction; make all changes persistent |
| Rollback | Undo a transaction; discard all changes when a failure or conflict occurs |
| SQLite | Embedded database file used for persistent storage; no separate server |
| Docker volume | Persistent storage that retains the database across application-container replacement when the same volume is reused |
| ADR | Architecture Decision Record; documents a decision with context, rationale and consequences |
| C4 | Context, Container, Component and Code; this project uses the first three levels |
