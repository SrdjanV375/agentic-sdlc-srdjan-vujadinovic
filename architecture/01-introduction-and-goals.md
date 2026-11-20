# 1. Introduction and Goals

## Requirements Overview

The CQRS Booking system supports hotel room availability searches and reservations for a single hotel.

**Functional Requirements:**

- FR1: Search available rooms by arrival and departure dates
- FR2: Book a room using these inputs:
  - client identifier
  - room name
  - arrival date
  - departure date
- FR3: Prevent overlapping reservations for the same room
- FR4: Maintain authoritative reservation storage (WriteRegistry) and an availability read projection (ReadRegistry)
- FR5: Provide separate command and query interfaces (CQRS pattern)

**Quality Goals:**

- Q1: Correctness (highest priority) — Prevent overlapping reservations and show accurate availability after a successful booking
- Q2: Simplicity — Small, understandable application using one modular application structure
- Q3: Testability — Business logic separated from Flask and testable with pytest
- Q4: Maintainability — Clear separation of command and query responsibilities
- Q5: Local development — Runs in Docker, tests execute in CI pipeline

## Stakeholders

| Role | Interest |
|------|----------|
| Hotel User | Searches for available rooms and books a room |
| Course Instructor | Evaluates implementation against kata requirements |
| Developer | Requires clear architecture and testability for CI/CD |
