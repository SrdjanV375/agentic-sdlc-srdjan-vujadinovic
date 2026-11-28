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


def _read_volume_tables(volume_name: str, db_path: str = "/data/test.db") -> dict:
    """Return the contents of rooms and availability tables from the volume.

    Runs a one-shot sidecar container so the read goes through the same
    filesystem path as the application, without opening the file on the host.
    Returns ``{"rooms": [...], "availability": [...]}`` with rows as tuples
    sorted deterministically.
    """
    # Build the read script. SQL is entirely hardcoded; db_path is a
    # test-controlled constant with no user input. nosec B608 on each line
    # that bandit flags for string-based SQL construction.
    script = (
        "import sqlite3, json;"  # nosec B608
        f"c=sqlite3.connect('{db_path}');"
        "rooms=sorted(c.execute('SELECT name FROM rooms ORDER BY name').fetchall());"  # nosec B608
        "avail=sorted(c.execute("  # nosec B608
        "'SELECT room_name,arrival,departure FROM availability"
        " ORDER BY room_name,arrival,departure').fetchall());"
        "print(json.dumps({'rooms': rooms, 'availability': avail}));"
        "c.close()"
    )
    result = subprocess.run(  # nosec B603 B607
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{volume_name}:/data",
            _IMAGE,
            "python",
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    import json

    data = json.loads(result.stdout.strip())
    return {
        "rooms": [tuple(r) for r in data["rooms"]],
        "availability": [tuple(r) for r in data["availability"]],
    }


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

        # Verify the first container serves the expected result before replacement.
        response_before = requests.get(
            base_url + "/availability",
            params={"arrival": "2027-06-11", "departure": "2027-06-14"},
            timeout=5,
        )
        assert response_before.status_code == 200
        assert "<li>B</li>" in response_before.text
        assert "<li>A</li>" not in response_before.text

        # Capture table contents from the volume before stopping the container.
        tables_before = _read_volume_tables(volume)

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

        # AND: Both tables contain exactly the same rows as before replacement.
        tables_after = _read_volume_tables(volume)
        assert tables_after["rooms"] == tables_before["rooms"]
        assert tables_after["availability"] == tables_before["availability"]
    finally:
        if container_id:
            _stop_container(container_id)
        _remove_volume(volume)


# ---------------------------------------------------------------------------
# AVAILABILITY-INFRA-001.3-S1
# ---------------------------------------------------------------------------


def test_availability_infra_001_3_s1_failed_search_logs_safely_no_internals():
    """AVAILABILITY-INFRA-001.3-S1: DB-read failure produces safe logs."""
    import re

    from cqrs_booking.app import create_app
    from cqrs_booking.availability import QueryService, ReadRegistry

    # GIVEN: Application logging is configured as it is at runtime, with the
    #        format used by create_app_from_env; the data store will raise on read.
    runtime_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
    # Timestamp pattern: YYYY-MM-DD HH:MM:SS,mmm
    timestamp_re = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+")

    conn = sqlite3.connect(":memory:")
    conn.close()  # closed connection → ProgrammingError on any execute

    registry = ReadRegistry(conn)
    service = QueryService(registry)
    app = create_app(query_service=service)

    # Capture formatted output from the cqrs_booking logger hierarchy,
    # using the same format string as create_app_from_env, without
    # attaching a test-only formatter and claiming it proves runtime config.
    formatted_lines = []

    class _FormattedCapture(logging.Handler):
        def __init__(self):
            super().__init__()
            self.setFormatter(logging.Formatter(runtime_format))

        def emit(self, record):
            formatted_lines.append(self.format(record))

    logger = logging.getLogger("cqrs_booking")
    original_level = logger.level
    handler = _FormattedCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        client = app.test_client()

        # WHEN: A valid search is submitted but the data store cannot be read.
        response = client.get(
            "/availability",
            query_string={"arrival": "2027-06-11", "departure": "2027-06-14"},
        )

        # THEN: Generic user feedback is returned.
        assert response.status_code == 200
        body = response.data.decode()
        assert "Unable to complete" in body

        # AND: No database internals are in the HTML response.
        assert "ProgrammingError" not in body
        assert "sqlite3" not in body
        assert "Cannot operate" not in body

        # AND: At least one application log record was emitted.
        assert formatted_lines, "Expected at least one log line from cqrs_booking"

        # AND: Every formatted log line has a timestamp, the component name,
        #      and a failure-level keyword — matching the runtime format.
        failure_line_found = False
        for line in formatted_lines:
            assert timestamp_re.match(line), f"Log line missing timestamp: {line!r}"
            assert "cqrs_booking" in line, f"Log line missing component name: {line!r}"
            if "availability search failure" in line:
                failure_line_found = True
                assert (
                    "ERROR" in line
                ), f"Failure log line must carry ERROR level: {line!r}"

        assert failure_line_found, "No log line contained 'availability search failure'"

        # AND: No log line contains exception internals or query parameters.
        all_output = "\n".join(formatted_lines)
        assert "Traceback" not in all_output
        assert "ProgrammingError" not in all_output
        assert "sqlite3" not in all_output
        assert "Cannot operate" not in all_output
        assert "2027-06-11" not in all_output, "Arrival date must not appear in logs"
        assert "2027-06-14" not in all_output, "Departure date must not appear in logs"

    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)


@pytest.mark.skipif(_SKIP_DOCKER, reason=_DOCKER_SKIP_REASON)
def test_availability_infra_001_3_s1_container_logs_no_query_params_on_failure():
    """AVAILABILITY-INFRA-001.3-S1: Container logs exclude query params on failure."""
    # The Flask test client does not exercise Werkzeug access logging.
    # This test verifies the actual container log via docker logs.

    # GIVEN: A running application container whose database will fail on read.
    #        We use a path that sqlite3 will open (creating the file) but whose
    #        schema is absent, so the first query raises OperationalError.
    volume = f"{_VOLUME_PREFIX}-diag-{uuid.uuid4().hex[:8]}"
    base_url = f"http://localhost:{_APP_PORT}"
    container_id = None
    try:
        _remove_volume(volume)
        # Start with a valid DB first so the app starts cleanly, then trigger
        # failure by pointing at a DB with no schema via a sidecar rename.
        # Simpler: start the app, then immediately break the DB file by
        # replacing it with an empty non-SQLite file via a sidecar container.
        container_id = _start_app_container(volume, _APP_PORT)
        _wait_for_http(base_url + "/availability")

        # Replace the DB on the volume with a corrupt file so the next read fails.
        subprocess.run(  # nosec B603 B607
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{volume}:/data",
                _IMAGE,
                "python",
                "-c",
                "open('/data/test.db','wb').write(b'not a sqlite file')",
            ],
            check=True,
            capture_output=True,
        )

        # WHEN: A search is submitted with query parameters after the DB is broken.
        import requests

        requests.get(
            base_url + "/availability",
            params={"arrival": "2027-06-11", "departure": "2027-06-14"},
            timeout=5,
        )

        # Collect the container log.
        log_result = subprocess.run(  # nosec B603 B607
            ["docker", "logs", container_id],
            capture_output=True,
            text=True,
        )
        container_log = log_result.stdout + log_result.stderr

        # THEN: The application failure line is present in the log.
        assert (
            "availability search failure" in container_log
        ), "Expected application failure log entry in container log"

        # AND: The failure line contains timestamp, component, level, message.
        import re

        ts_re = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+")
        failure_line = next(
            (
                line
                for line in container_log.splitlines()
                if "availability search failure" in line
            ),
            None,
        )
        assert failure_line is not None
        assert ts_re.search(
            failure_line
        ), f"Failure line missing timestamp: {failure_line!r}"
        assert (
            "cqrs_booking.app" in failure_line
        ), f"Failure line missing component: {failure_line!r}"
        assert (
            "ERROR" in failure_line
        ), f"Failure line missing ERROR level: {failure_line!r}"

        # AND: No traceback or database exception details appear in the log.
        assert "Traceback" not in container_log
        assert "ProgrammingError" not in container_log
        assert "OperationalError" not in container_log
        assert "sqlite3" not in container_log

        # AND: The query parameters do not appear in any log line.
        for line in container_log.splitlines():
            assert (
                "2027-06-11" not in line
            ), f"Arrival date leaked into container log line: {line!r}"
            assert (
                "2027-06-14" not in line
            ), f"Departure date leaked into container log line: {line!r}"

    finally:
        if container_id:
            _stop_container(container_id)
        _remove_volume(volume)
