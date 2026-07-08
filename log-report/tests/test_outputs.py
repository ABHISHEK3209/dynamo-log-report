import json
from pathlib import Path

REPORT = Path("/app/report.json")
REQUIRED_KEYS = {"total_requests", "unique_ips", "top_path"}


def load_report():
    return json.loads(REPORT.read_text())


def test_report_schema():
    """Criterion 1: /app/report.json exists and is a JSON object whose keys are
    exactly total_requests, unique_ips, and top_path."""
    assert REPORT.exists(), "no report.json found"
    data = load_report()
    assert isinstance(data, dict), "report.json must be a JSON object"
    assert set(data.keys()) == REQUIRED_KEYS, f"unexpected keys: {sorted(data.keys())}"


def test_total_requests():
    """Criterion 2: total_requests equals the number of non-empty request lines
    in /app/access.log (6)."""
    data = load_report()
    assert data["total_requests"] == 6


def test_unique_ips():
    """Criterion 3: unique_ips equals the number of distinct client IPs
    in /app/access.log (3)."""
    data = load_report()
    assert data["unique_ips"] == 3


def test_top_path():
    """Criterion 4: top_path equals the most frequently requested path
    in /app/access.log (/index.html)."""
    data = load_report()
    assert data["top_path"] == "/index.html"
