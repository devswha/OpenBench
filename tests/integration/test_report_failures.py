from __future__ import annotations

from pathlib import Path

from openbench.reporters.html_reporter import StaticHtmlReporter
from openbench.reporters.parser import parse_runtime_report


def test_report_renders_failure_states(tmp_path) -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-partial-failure")
    parsed = parse_runtime_report(fixture_dir)

    output_path = StaticHtmlReporter().write(parsed.report, tmp_path / "report.html")
    html = output_path.read_text()

    assert "GNU time is not available" in html
    assert "SETUP_ERROR" in html
    assert "Unavailable" in html
