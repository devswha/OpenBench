from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import shutil
from tempfile import NamedTemporaryFile
import time
from typing import Iterable

from openbench.models import DoctorCheck, RunStatus
from openbench.utils.process import combine_output, run_subprocess


@dataclass(slots=True)
class Measurement:
    status: RunStatus
    output: str
    raw: dict[str, object]
    exit_code: int = 0
    error_message: str | None = None
    peak_memory_mb: float | None = None
    duration_ms: int = 0


def _resolve_explicit_or_candidate(value: str) -> str | None:
    path = Path(value)
    if path.exists() and path.is_file():
        return str(path.resolve())
    return shutil.which(value)


def resolve_tool(env_var: str, candidates: Iterable[str]) -> str | None:
    override = os.environ.get(env_var)
    if override:
        return _resolve_explicit_or_candidate(override)

    for candidate in candidates:
        resolved = _resolve_explicit_or_candidate(candidate)
        if resolved:
            return resolved
    return None


def discover_runtime_tools() -> dict[str, str | None]:
    return {
        "hyperfine": resolve_tool("OPENBENCH_HYPERFINE_BIN", ["hyperfine"]),
        "time": resolve_tool("OPENBENCH_TIME_BIN", ["/usr/bin/time", "gtime", "time"]),
        "du": resolve_tool("OPENBENCH_DU_BIN", ["du"]),
    }


def doctor_checks() -> list[DoctorCheck]:
    tools = discover_runtime_tools()
    return [
        DoctorCheck(name=f"runtime {name}", ok=path is not None, details=path or "missing", category="runtime")
        for name, path in tools.items()
    ]


def measure_startup(command_path: str, timeout: int) -> Measurement:
    hyperfine_bin = discover_runtime_tools()["hyperfine"]
    if hyperfine_bin is None:
        return Measurement(
            status=RunStatus.SETUP_ERROR,
            output="",
            raw={"metric": "startup_ms", "available": False, "unit": "ms"},
            error_message="hyperfine is not available",
        )

    with NamedTemporaryFile(prefix="openbench-hyperfine-", suffix=".json", delete=False) as temporary_file:
        export_path = Path(temporary_file.name)
    quoted_command = shlex.join([command_path, "--version"])
    started = time.perf_counter()
    completed = run_subprocess(
        [hyperfine_bin, "--warmup", "1", "--export-json", str(export_path), quoted_command],
        timeout=timeout,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    output = combine_output(completed)

    try:
        payload = json.loads(export_path.read_text())
        mean_seconds = float(payload["results"][0]["mean"])
    except (FileNotFoundError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return Measurement(
            status=RunStatus.FAILED,
            output=output,
            raw={"metric": "startup_ms", "available": False, "unit": "ms"},
            exit_code=completed.returncode,
            error_message=f"failed to parse hyperfine output: {exc}",
            duration_ms=duration_ms,
        )
    finally:
        export_path.unlink(missing_ok=True)

    return Measurement(
        status=RunStatus.SUCCESS,
        output=output,
        raw={
            "metric": "startup_ms",
            "available": True,
            "value": mean_seconds * 1000.0,
            "unit": "ms",
            "command": quoted_command,
        },
        exit_code=completed.returncode,
        duration_ms=duration_ms,
    )


def measure_memory(command_path: str, timeout: int) -> Measurement:
    time_bin = discover_runtime_tools()["time"]
    if time_bin is None:
        return Measurement(
            status=RunStatus.SETUP_ERROR,
            output="",
            raw={"metric": "memory_mb", "available": False, "unit": "MB"},
            error_message="GNU time is not available",
        )

    started = time.perf_counter()
    completed = run_subprocess([time_bin, "-v", command_path, "--version"], timeout=timeout)
    duration_ms = int((time.perf_counter() - started) * 1000)
    output = combine_output(completed)

    match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", completed.stderr)
    if not match:
        return Measurement(
            status=RunStatus.FAILED,
            output=output,
            raw={"metric": "memory_mb", "available": False, "unit": "MB"},
            exit_code=completed.returncode,
            error_message="failed to parse maximum resident set size",
            duration_ms=duration_ms,
        )

    peak_memory_mb = int(match.group(1)) / 1024.0
    return Measurement(
        status=RunStatus.SUCCESS,
        output=output,
        raw={"metric": "memory_mb", "available": True, "value": peak_memory_mb, "unit": "MB"},
        exit_code=completed.returncode,
        peak_memory_mb=peak_memory_mb,
        duration_ms=duration_ms,
    )


def measure_binary_size(command_path: str) -> Measurement:
    du_bin = discover_runtime_tools()["du"]
    if du_bin is None:
        return Measurement(
            status=RunStatus.SETUP_ERROR,
            output="",
            raw={"metric": "binary_size_mb", "available": False, "unit": "MB"},
            error_message="du is not available",
        )

    started = time.perf_counter()
    completed = run_subprocess([du_bin, "-sb", command_path], timeout=15)
    duration_ms = int((time.perf_counter() - started) * 1000)
    output = combine_output(completed)

    try:
        size_bytes = int((completed.stdout or "").split()[0])
    except (IndexError, ValueError) as exc:
        return Measurement(
            status=RunStatus.FAILED,
            output=output,
            raw={"metric": "binary_size_mb", "available": False, "unit": "MB"},
            exit_code=completed.returncode,
            error_message=f"failed to parse binary size: {exc}",
            duration_ms=duration_ms,
        )

    size_mb = size_bytes / (1024.0 * 1024.0)
    return Measurement(
        status=RunStatus.SUCCESS,
        output=output,
        raw={
            "metric": "binary_size_mb",
            "available": True,
            "value": size_mb,
            "value_bytes": size_bytes,
            "unit": "MB",
        },
        exit_code=completed.returncode,
        duration_ms=duration_ms,
    )
