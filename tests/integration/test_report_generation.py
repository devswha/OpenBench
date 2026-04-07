from __future__ import annotations

from pathlib import Path

from openbench.reporters.html_reporter import StaticHtmlReporter
from openbench.reporters.parser import parse_runtime_report


def test_report_html_is_generated(tmp_path) -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-success")
    parsed = parse_runtime_report(fixture_dir)

    output_path = StaticHtmlReporter().write(parsed.report, tmp_path / "report.html")

    assert output_path.exists()
    html = output_path.read_text()
    assert "OpenBench Benchmark Report" in html
    assert "runtime-success" in html


def test_report_contains_agent_names_and_metrics(tmp_path) -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-success")
    parsed = parse_runtime_report(fixture_dir)

    output_path = StaticHtmlReporter().write(parsed.report, tmp_path / "report.html")
    html = output_path.read_text()

    assert "omc" in html
    assert "omx" in html
    assert "Startup" in html
    assert "Memory" in html
    assert "Binary size" in html
    assert "Linux-test" in html
    assert "3.11.15" in html
    assert "Practical task summary" in html
    assert "single-file-bug-fix" in html
    assert "5/5 passed" in html
