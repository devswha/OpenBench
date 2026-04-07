from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_readme_mentions_report_workflow() -> None:
    readme = Path("README.md").read_text()
    assert "openbench report --format html" in readme


def test_report_smoke(tmp_path) -> None:
    output_path = tmp_path / "report.html"
    command = [
        sys.executable,
        "-m",
        "openbench.cli",
        "report",
        "--format",
        "html",
        "--input",
        "tests/fixtures/results/runtime-success",
        "--output",
        str(output_path),
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=os.environ.copy())

    assert completed.returncode == 0, completed.stdout + completed.stderr
    html = output_path.read_text()
    assert "OpenBench Runtime Report" in html
    assert "omc" in html
    assert "omx" in html
