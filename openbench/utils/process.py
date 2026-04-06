from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Mapping


def run_subprocess(
    args: list[str],
    *,
    timeout: int = 30,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=dict(env) if env is not None else None,
        cwd=str(cwd) if cwd is not None else None,
    )


def combine_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()
