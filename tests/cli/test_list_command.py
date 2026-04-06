from __future__ import annotations

from click.testing import CliRunner

from openbench.cli import main


def test_list_agents_shows_omc() -> None:
    result = CliRunner().invoke(main, ["list", "agents"])

    assert result.exit_code == 0
    assert "omc" in result.output
    assert "omx" in result.output


def test_list_suites_shows_runtime() -> None:
    result = CliRunner().invoke(main, ["list", "suites"])

    assert result.exit_code == 0
    assert "runtime" in result.output
