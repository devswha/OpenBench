from __future__ import annotations

from click.testing import CliRunner

from openbench.cli import main


def test_doctor_reports_ready_state(shim_env, tmp_path) -> None:
    result = CliRunner().invoke(main, ["doctor", "--results-dir", str(tmp_path / "results")])

    assert result.exit_code == 0
    assert "Environment ready." in result.output
    assert "[OK]" in result.output
    assert "agent:omc command" in result.output
    assert "agent:omx command" in result.output


def test_doctor_reports_missing_tool(monkeypatch, shim_env, tmp_path) -> None:
    monkeypatch.setenv("OPENBENCH_HYPERFINE_BIN", str(tmp_path / "missing-hyperfine"))

    result = CliRunner().invoke(main, ["doctor", "--results-dir", str(tmp_path / "results")])

    assert result.exit_code == 1
    assert "Environment not ready." in result.output
    assert "runtime:runtime hyperfine" in result.output
