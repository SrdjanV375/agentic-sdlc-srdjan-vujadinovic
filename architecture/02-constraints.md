# 2. Architecture Constraints

## Kata and Course Constraints

- **CQRS Pattern** — The kata requires separate Command Service, WriteRegistry, ReadRegistry and Query Service components [CQRS_Booking kata](https://codingdojo.org/kata/CQRS_Booking/)
- **Single Hotel** — The system serves reservations for one hotel only [CQRS_Booking kata](https://codingdojo.org/kata/CQRS_Booking/)
- **ReadRegistry Notification** — The Command Service calls WriteRegistry, which notifies ReadRegistry. [CQRS_Booking kata](https://codingdojo.org/kata/CQRS_Booking/)
- **pytest and Docker** — Tests must run via pytest and execute in a Docker environment for CI/CD [Module 4: Docker and CI](https://github.com/LabSoft-AI/Agentic-SDLC-Software-Factory-2026-11-16/blob/main/modules/module-4-cicd/README.md), [Module 5: pytest and TDD](https://github.com/LabSoft-AI/Agentic-SDLC-Software-Factory-2026-11-16/blob/main/modules/module-5-tdd-bdd/README.md)
- **arc42 and PlantUML** — Architecture documentation follows the arc42 template with C4 diagrams [Module 2: Architecture](https://github.com/LabSoft-AI/Agentic-SDLC-Software-Factory-2026-11-16/blob/main/modules/module-2-architecture/README.md), [Module 6: Final project documentation](https://github.com/LabSoft-AI/Agentic-SDLC-Software-Factory-2026-11-16/blob/main/modules/module-6-project/README.md)
- **Local Docker Deployment** — The application runs locally in Docker. GitHub Actions builds and tests the project. Module 6 requires Sphinx documentation on GitHub Pages; GitHub Pages does not host the Flask application.

## Accepted Project Decisions

See [ADR-001](09-architecture-decisions.md) for technology and structural choices:
- Python 3.12, Flask, HTML/CSS, SQLite, pytest and local Docker execution
- One modular application with command and query separation
- Synchronous read-projection updates within the booking transaction
