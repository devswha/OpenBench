from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_cli_run_runtime_persists_results_via_module(agent_name: str, shim_env, tmp_path) -> None:
    env = os.environ.copy()
    env["OPENBENCH_HYPERFINE_BIN"] = shim_env["OPENBENCH_HYPERFINE_BIN"]
    env["OPENBENCH_TIME_BIN"] = shim_env["OPENBENCH_TIME_BIN"]
    env["OPENBENCH_DU_BIN"] = shim_env["OPENBENCH_DU_BIN"]
    env["OPENBENCH_OMX_COMMAND"] = shim_env["OPENBENCH_OMX_COMMAND"]

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "openbench.cli",
            "run",
            "--agent",
            agent_name,
            "--suite",
            "runtime",
            "--results-dir",
            str(tmp_path / "results"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    run_dirs = list((tmp_path / "results").iterdir())
    payload = json.loads((run_dirs[0] / agent_name / "runtime.json").read_text())
    assert payload["agent"] == agent_name
