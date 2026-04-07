from __future__ import annotations

from pathlib import Path

from openbench.reporters.html_reporter import StaticHtmlReporter
from openbench.reporters.parser import parse_runtime_report


def test_report_generation_is_deterministic() -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-success")
    report = parse_runtime_report(fixture_dir).report
    reporter = StaticHtmlReporter()

    first = reporter.render(report)
    second = reporter.render(report)

    assert first == second
