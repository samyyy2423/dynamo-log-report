import json
from pathlib import Path

import pytest

REPORT = Path("/app/report.json")


@pytest.fixture(scope="module")
def report():
    """Load the report; failure here means criterion 1 is unmet."""
    assert REPORT.exists(), "no report.json at /app/report.json"
    with REPORT.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "report.json must be a single JSON object"
    return data


def test_report_is_json_object():
    """Criterion 1: /app/report.json exists and contains a single JSON object."""
    assert REPORT.exists(), "no report.json at /app/report.json"
    with REPORT.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "report.json must be a single JSON object"


def test_total_requests(report):
    """Criterion 2: total_requests equals the number of request lines (6)."""
    assert report["total_requests"] == 6


def test_unique_ips(report):
    """Criterion 3: unique_ips equals the count of distinct client IPs (3)."""
    assert report["unique_ips"] == 3


def test_top_path(report):
    """Criterion 4: top_path is the most frequently requested path (/index.html)."""
    assert report["top_path"] == "/index.html"
