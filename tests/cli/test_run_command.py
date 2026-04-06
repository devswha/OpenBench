from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from openbench.cli import main


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_run_command_persists_runtime_results(agent_name: str, shim_env, tmp_path) -> None:
    result = CliRunner().invoke(
        main,
        ["run", "--agent", agent_name, "--suite", "runtime", "--results-dir", str(tmp_path / "results")],
    )

    assert result.exit_code == 0
    run_dirs = list((tmp_path / "results").iterdir())
    assert len(run_dirs) == 1
    report_path = run_dirs[0] / agent_name / "runtime.json"
    payload = json.loads(report_path.read_text())
    assert payload["suite"] == "runtime"
    assert payload["agent"] == agent_name
