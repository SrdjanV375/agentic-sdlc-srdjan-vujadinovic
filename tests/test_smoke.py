"""Check that the project package can be imported."""

import importlib
import sys
from pathlib import Path


def test_application_package_is_importable():
    source_directory = Path(__file__).resolve().parents[1] / "src"
    sys.path.insert(0, str(source_directory))
    try:
        package = importlib.import_module("cqrs_booking")
        assert package.__doc__ == "CQRS Booking application package."
    finally:
        sys.path.pop(0)
