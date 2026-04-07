from __future__ import annotations

import os
import subprocess
import sys


def test_practical_fixtures_are_reproducible(shim_env, tmp_path) -> None:
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
            "omc",
            "--suite",
            "practical",
            "--results-dir",
            str(tmp_path / "results"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
