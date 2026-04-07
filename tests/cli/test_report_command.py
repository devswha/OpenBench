from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from openbench.cli import main


def test_report_command_generates_html(tmp_path) -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-success")
    output_path = tmp_path / "report.html"

    result = CliRunner().invoke(
        main,
        ["report", "--format", "html", "--input", str(fixture_dir), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert "Report written:" in result.output


def test_report_command_rejects_invalid_run_dir(tmp_path) -> None:
    fixture_dir = Path("tests/fixtures/results/runtime-invalid")
    output_path = tmp_path / "report.html"

    result = CliRunner().invoke(
        main,
        ["report", "--format", "html", "--input", str(fixture_dir), "--output", str(output_path)],
    )

    assert result.exit_code != 0
    assert "Missing runtime.json for agent 'omx'" in result.output
