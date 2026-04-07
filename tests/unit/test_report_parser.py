from __future__ import annotations

from pathlib import Path

import pytest

from openbench.reporters.parser import ReportInputError, parse_runtime_report


def test_report_contract_parses_success_fixture() -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-success")

    parsed = parse_runtime_report(fixture_dir)

    assert parsed.report.run_id == "runtime-success"
    assert [agent.agent_name for agent in parsed.report.agents] == ["omc", "omx"]
    assert [metric.key for metric in parsed.report.agents[0].metrics] == [
        "startup_ms",
        "memory_mb",
        "binary_size_mb",
    ]


def test_report_rejects_invalid_run_dir() -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-invalid")

    with pytest.raises(ReportInputError):
        parse_runtime_report(fixture_dir)
