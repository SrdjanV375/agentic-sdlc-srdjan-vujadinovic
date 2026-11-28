# CQRS Booking — Story Inventory

## Domains and Architecture References

| Domain | Major components | Architecture |
|--------|------------------|--------------|
| AVAILABILITY | Query Service, ReadRegistry | [Chapter 5: Components](../../architecture/05-building-block-view.md#components) |
| BOOKING | Command Service, WriteRegistry, ReadRegistry | [Chapter 5: Components](../../architecture/05-building-block-view.md#components) |

Domains map to CQRS components. The Web Interface supports both domains via HTTP routes ([Chapter 3](../../architecture/03-context-and-scope.md#browser-to-application-communication-proposed-routes)).

## Prioritized Stories

| Priority | Story ID | User story | Core | Bundle status | Dependencies |
|----------|----------|------------|------|---------------|--------------|
| 1 | AVAILABILITY-STORY-001 | AS A Hotel User I WANT to find available rooms for my arrival and departure dates SO THAT I can choose a room for my stay. | Yes | Approved | None |
| 2 | BOOKING-STORY-001 | AS A Hotel User I WANT to reserve an available room using my client identifier and stay dates SO THAT the room is reserved for my stay. | Yes | Approved | None |

**Pareto rationale:**

Both original stories are core because together they cover the kata's main search-and-book workflow. Each has independent value:
- Search delivers standalone value by showing availability before booking.
- Booking delivers standalone value by allowing reservations without requiring a prior search; it validates availability against authoritative WriteRegistry data.

Supporting requirements (validation, persistence, logging, consistency) are covered by scenarios and appropriate FE/BE/INFRA sub-stories. Both availability and booking sub-stories are approved. See sub-story inventory below.

## Pareto Prioritization

**Inventory:** 2 original stories.

**Core:** 2 stories (100%).

**Supporting:** 0 stories.

**Ratio:** 2/2 = 100%.

This 100% core ratio departs from the course's approximate 20% target because the architecture defines only two essential user workflows. Neither story was split or invented to force a ratio; both represent distinct, necessary user-facing functionality in the kata scope.

## Progress

- Core story bundles reviewed and approved: 2/2
- Core stories implemented and verified: 1/2
- Requirements approval does not imply implementation completion.

### Bundle Documentation Status

| Story ID | Status |
|----------|--------|
| AVAILABILITY-STORY-001 | Approved |
| BOOKING-STORY-001 | Approved |

### Implementation Progress

| Story ID | Domain | INFRA | BE | FE | E2E |
|----------|--------|-------|----|----|-----|
| AVAILABILITY-STORY-001 | AVAILABILITY | Implemented and verified | Implemented and verified | Implemented and verified | Implemented and verified |
| BOOKING-STORY-001 | BOOKING | Not started | Not started | Not started | Not started |

Implementation order: INFRA → BE → FE → original-story E2E verification.

## Sub-Story Inventory

### Existing (from manual bundle)

| Story ID | Type | Parent | Status |
|----------|------|--------|--------|
| AVAILABILITY-FE-001.1 | FE | AVAILABILITY-STORY-001 | Approved |
| AVAILABILITY-BE-001.1 | BE | AVAILABILITY-STORY-001 | Approved |
| AVAILABILITY-INFRA-001.1 | INFRA | AVAILABILITY-STORY-001 | Approved |
| AVAILABILITY-INFRA-001.2 | INFRA | AVAILABILITY-STORY-001 | Approved |
| AVAILABILITY-INFRA-001.3 | INFRA | AVAILABILITY-STORY-001 | Approved |

### Existing (booking bundle approved for documentation)

| Story ID | Type | Parent | Status |
|----------|------|--------|--------|
| BOOKING-FE-001.1 | FE | BOOKING-STORY-001 | Approved |
| BOOKING-BE-001.1 | BE | BOOKING-STORY-001 | Approved |
| BOOKING-INFRA-001.1 | INFRA | BOOKING-STORY-001 | Approved |
| BOOKING-INFRA-001.2 | INFRA | BOOKING-STORY-001 | Approved |
| BOOKING-INFRA-001.3 | INFRA | BOOKING-STORY-001 | Approved |

## Resolved Requirements

- **Date boundary rule**: Resolved by user agreement. Arrival is inclusive, departure is exclusive. A new stay may start on the previous stay's departure date. See [availability.md](./availability.md#date-boundary-rule).

## Open Requirements

- No open requirements for the availability domain.
