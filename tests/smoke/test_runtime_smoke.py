from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_readme_quickstart_matches_cli_surface() -> None:
    readme = Path("README.md").read_text()
    assert "openbench doctor" in readme
    assert "openbench list agents" in readme
    assert "openbench list suites" in readme
    assert "openbench run --agent omc --suite runtime" in readme
    assert "openbench run --agent omx --suite runtime" in readme
    assert "openbench report --format html" in readme


def test_runtime_smoke(shim_env, tmp_path) -> None:
    env = os.environ.copy()
    env["OPENBENCH_HYPERFINE_BIN"] = shim_env["OPENBENCH_HYPERFINE_BIN"]
    env["OPENBENCH_TIME_BIN"] = shim_env["OPENBENCH_TIME_BIN"]
    env["OPENBENCH_DU_BIN"] = shim_env["OPENBENCH_DU_BIN"]
    env["OPENBENCH_OMX_COMMAND"] = shim_env["OPENBENCH_OMX_COMMAND"]

    commands = [
        [sys.executable, "-m", "openbench.cli", "list", "agents"],
        [sys.executable, "-m", "openbench.cli", "list", "suites"],
        [sys.executable, "-m", "openbench.cli", "doctor", "--results-dir", str(tmp_path / "results")],
        [
            sys.executable,
            "-m",
            "openbench.cli",
            "run",
            "--agent",
            "omc",
            "--suite",
            "runtime",
            "--results-dir",
            str(tmp_path / "results"),
        ],
        [
            sys.executable,
            "-m",
            "openbench.cli",
            "run",
            "--agent",
            "omx",
            "--suite",
            "runtime",
            "--results-dir",
            str(tmp_path / "results-omx"),
        ],
    ]

    for command in commands:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
        assert completed.returncode == 0, completed.stdout + completed.stderr
