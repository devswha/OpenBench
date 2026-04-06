from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def fixture_bin_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "bin"


@pytest.fixture()
def shim_env(monkeypatch: pytest.MonkeyPatch, fixture_bin_dir: Path, tmp_path: Path) -> dict[str, str]:
    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{fixture_bin_dir}{os.pathsep}{original_path}")
    monkeypatch.setenv("OPENBENCH_HYPERFINE_BIN", str(fixture_bin_dir / "hyperfine"))
    monkeypatch.setenv("OPENBENCH_TIME_BIN", str(fixture_bin_dir / "openbench-time"))
    monkeypatch.setenv("OPENBENCH_DU_BIN", str(fixture_bin_dir / "du"))
    monkeypatch.setenv("OPENBENCH_OMX_COMMAND", str(fixture_bin_dir / "omx"))
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    return {
        "RESULTS_DIR": str(tmp_path / "results"),
        "PATH": os.environ["PATH"],
        "OPENBENCH_HYPERFINE_BIN": str(fixture_bin_dir / "hyperfine"),
        "OPENBENCH_TIME_BIN": str(fixture_bin_dir / "openbench-time"),
        "OPENBENCH_DU_BIN": str(fixture_bin_dir / "du"),
        "OPENBENCH_OMX_COMMAND": str(fixture_bin_dir / "omx"),
    }
