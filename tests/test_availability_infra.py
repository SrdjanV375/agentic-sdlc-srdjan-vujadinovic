"""Infrastructure scenarios for AVAILABILITY-STORY-001.

These tests verify deployment, persistence, and diagnostics.
INFRA-001.1-S1 and INFRA-001.2-S1 require a Docker daemon and the
``requests`` library; they are skipped automatically when either is absent
so the default container test suite (which has no Docker socket) stays green.
INFRA-001.3-S1 is a pure-Python diagnostic test and runs everywhere.
"""

import importlib.util
import logging
import sqlite3
import subprocess  # nosec B404
import time
import uuid

import pytest

# ---------------------------------------------------------------------------
# Shared skip guard for Docker-dependent tests
# ---------------------------------------------------------------------------

_REQUESTS_AVAILABLE = importlib.util.find_spec("requests") is not None


def _docker_available() -> bool:
    try:
        result = subprocess.run(  # nosec B603 B607
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


_SKIP_DOCKER = not (_REQUESTS_AVAILABLE and _docker_available())
_DOCKER_SKIP_REASON = (
    "Docker daemon or 'requests' library not available" if _SKIP_DOCKER else ""
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IMAGE = "kata-tests"
_APP_PORT = 15180  # fixed test port — unlikely to collide
_VOLUME_PREFIX = "avail-infra-test"


def _start_app_container(
    volume_name: str,
    host_port: int,
    db_path: str = "/data/test.db",
) -> str:
    """Start the application container; return the container ID."""
    result = subprocess.run(  # nosec B603 B607
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            f"{host_port}:5000",
            "-v",
            f"{volume_name}:/data",
            "-e",
            f"DATABASE_PATH={db_path}",
            _IMAGE,
            "python",
            "-m",
            "cqrs_booking",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _stop_container(container_id: str) -> None:
    subprocess.run(  # nosec B603 B607
        ["docker", "stop", container_id],
        capture_output=True,
        timeout=15,
    )


def _wait_for_http(url: str, timeout: int = 15) -> None:
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(url, timeout=1)
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"Application at {url} did not become ready in {timeout}s")


def _remove_volume(volume_name: str) -> None:
    subprocess.run(  # nosec B603 B607
        ["docker", "volume", "rm", "-f", volume_name],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# AVAILABILITY-INFRA-001.1-S1
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_SKIP_DOCKER, reason=_DOCKER_SKIP_REASON)
def test_availability_infra_001_1_s1_reach_the_search_interface():
    """AVAILABILITY-INFRA-001.1-S1: Container serves the search form."""
    import requests

    # GIVEN: The application image is built; a fresh volume holds the database;
    #        the application port is published on the local host.
    volume = f"{_VOLUME_PREFIX}-{uuid.uuid4().hex[:8]}"
    base_url = f"http://localhost:{_APP_PORT}"
    container_id = None
    try:
        _remove_volume(volume)
        container_id = _start_app_container(volume, _APP_PORT)
        _wait_for_http(base_url + "/availability")

        # WHEN: The user navigates to the booking route.
        response = requests.get(base_url + "/availability", timeout=5)

        # THEN: HTTP 200 and the HTML search form is returned.
        assert response.status_code == 200
        assert "<form" in response.text
        assert 'name="arrival"' in response.text
        assert 'name="departure"' in response.text
    finally:
        if container_id:
            _stop_container(container_id)
        _remove_volume(volume)


# ---------------------------------------------------------------------------
# AVAILABILITY-INFRA-001.2-S1
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_SKIP_DOCKER, reason=_DOCKER_SKIP_REASON)
def test_availability_infra_001_2_s1_reuse_stored_data_after_container_replace():
    """AVAILABILITY-INFRA-001.2-S1: Stored data survives container replacement."""
    import requests

    # GIVEN: A named volume holds the SQLite database with rooms and reservations.
    volume = f"{_VOLUME_PREFIX}-persist-{uuid.uuid4().hex[:8]}"
    base_url = f"http://localhost:{_APP_PORT}"
    container_id = None
    try:
        _remove_volume(volume)

        # Start first container; schema is created by the app on startup.
        container_id = _start_app_container(volume, _APP_PORT)
        _wait_for_http(base_url + "/availability")

        # Seed: Room A reserved 2027-06-10–2027-06-15, Room B free.
        seed_result = subprocess.run(  # nosec B603 B607
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{volume}:/data",
                _IMAGE,
                "python",
                "-c",
                (
                    "import sqlite3;"
                    "c=sqlite3.connect('/data/test.db');"
                    "c.executescript("
                    "\"INSERT OR IGNORE INTO rooms(name) VALUES('A'),('B');"
                    "INSERT OR IGNORE INTO availability(room_name,arrival,departure)"
                    " VALUES('A','2027-06-10','2027-06-15');\""
                    ");"
                    "c.commit();"
                    "c.close()"
                ),
            ],
            capture_output=True,
            text=True,
        )
        assert seed_result.returncode == 0, seed_result.stderr

        _stop_container(container_id)
        container_id = None
        time.sleep(1)

        # WHEN: The container is replaced using the same volume.
        container_id = _start_app_container(volume, _APP_PORT)
        _wait_for_http(base_url + "/availability")

        response = requests.get(
            base_url + "/availability",
            params={"arrival": "2027-06-11", "departure": "2027-06-14"},
            timeout=5,
        )

        # THEN: The same search returns the same result; B available, A not.
        assert response.status_code == 200
        assert "<li>B</li>" in response.text
        assert "<li>A</li>" not in response.text
    finally:
        if container_id:
            _stop_container(container_id)
        _remove_volume(volume)


# ---------------------------------------------------------------------------
# AVAILABILITY-INFRA-001.3-S1
# ---------------------------------------------------------------------------


def test_availability_infra_001_3_s1_failed_search_logs_safely_no_internals():
    """AVAILABILITY-INFRA-001.3-S1: DB-read failure produces safe logs."""
    from cqrs_booking.app import create_app
    from cqrs_booking.availability import QueryService, ReadRegistry

    # GIVEN: Application logging is enabled; the data store will raise on read.
    conn = sqlite3.connect(":memory:")
    conn.close()  # closed connection → OperationalError on any execute

    registry = ReadRegistry(conn)
    service = QueryService(registry)
    app = create_app(query_service=service)

    log_records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    handler = _Capture()
    logger = logging.getLogger("cqrs_booking")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        client = app.test_client()

        # WHEN: A valid search is submitted but the data store cannot be read.
        response = client.get(
            "/availability",
            query_string={"arrival": "2027-06-11", "departure": "2027-06-14"},
        )

        # THEN: Generic feedback is returned; no database internals exposed.
        assert response.status_code == 200
        body = response.data.decode()
        assert "Unable to complete" in body
        assert "ProgrammingError" not in body
        assert "sqlite3" not in body
        assert "Cannot operate" not in body

        # AND: At least one log record captures component + failure outcome.
        assert log_records, "Expected at least one log record from cqrs_booking"
        messages = [r.getMessage() for r in log_records]
        combined = " ".join(messages).lower()
        assert "availab" in combined, "Log must reference the availability component"
        assert (
            "fail" in combined or "error" in combined
        ), "Log must record a failure outcome"

        # AND: Logs exclude client identifiers and booking details.
        for record in log_records:
            msg = record.getMessage()
            assert "2027-06-11" not in msg, "Log must not contain arrival date"
            assert "2027-06-14" not in msg, "Log must not contain departure date"
    finally:
        logger.removeHandler(handler)
