from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from openbench.cli import main


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_run_practical_suite_from_cli(agent_name: str, shim_env, tmp_path) -> None:
    result = CliRunner().invoke(
        main,
        ["run", "--agent", agent_name, "--suite", "practical", "--results-dir", str(tmp_path / "results")],
    )

    assert result.exit_code == 0
    run_dirs = list((tmp_path / "results").iterdir())
    report_path = run_dirs[0] / agent_name / "practical.json"
    payload = json.loads(report_path.read_text())
    assert payload["suite"] == "practical"
    assert payload["summary"]["failed_tasks"] == 0

