# 11. Risks and Technical Debts

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite write contention under concurrent booking requests | Reduced throughput; potential timeout errors | Serialize write transactions; consider load limits for local deployment |
| Incorrect transaction handling causing overlapping bookings or inconsistent read projections | Data corruption; double-booking | Authoritative overlap checking inside the serialized transaction; atomic reservation and projection updates; thorough integration tests |
| Loss of booking data if the persistent volume is deleted or incorrectly configured | Complete data loss | Document local volume configuration and provide manual backup/restore procedure |
| Missing authentication: client identifiers do not establish verified identity | No user isolation; any valid identifier can book any room | This is a project scope decision, not a mandatory kata limitation |
| Date-boundary rule: arrival is inclusive, departure is exclusive; a new stay may start on the previous stay's departure date | Boundary case in availability search and booking | Validate arrival before departure; use inclusive arrival and exclusive departure logic in date comparisons; thorough integration tests covering boundary dates |

These are architectural risks, limitations and open questions. No implementation technical debt has been identified at this stage.
