from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
import shutil

from openbench.models import DoctorCheck, RunResult, Task
from openbench.models import RunStatus
from openbench.suites.runtime.measurements import measure_binary_size, measure_memory, measure_startup
from openbench.utils.process import combine_output, run_subprocess


class AgentAdapter(ABC):
    name: str
    display_name: str
    version: str = "unknown"
    command: str

    def __init__(self, command: str | None = None) -> None:
        if command is not None:
            self.command = command

    def resolve_command(self) -> str | None:
        candidate = self.command
        if not candidate:
            return None

        if os.path.sep in candidate or candidate.startswith("."):
            path = Path(candidate)
            if path.exists() and os.access(path, os.X_OK):
                return str(path.resolve())
            return None

        return shutil.which(candidate)

    def health_check(self) -> bool:
        return self.resolve_command() is not None

    def doctor_checks(self) -> list[DoctorCheck]:
        resolved = self.resolve_command()
        details = resolved or f"'{self.command}' not found on PATH"
        return [DoctorCheck(name=f"{self.name} command", ok=resolved is not None, details=details, category="agent")]

    def detect_version(self) -> str:
        resolved = self.resolve_command()
        if not resolved:
            return "unavailable"

        completed = run_subprocess([resolved, "--version"], timeout=10)
        output = combine_output(completed)
        if not output:
            return "unknown"
        return output.splitlines()[0].strip()

    def setup(self) -> None:
        return None

    def cleanup(self) -> None:
        return None

    @abstractmethod
    def run(self, task: Task) -> RunResult:
        raise NotImplementedError


class RuntimeCommandAgent(AgentAdapter):
    def run(self, task: Task) -> RunResult:
        resolved_command = self.resolve_command()
        if resolved_command is None:
            return RunResult(
                task=task,
                status=RunStatus.SETUP_ERROR,
                output="",
                error_message=f"Agent command '{self.command}' is not available",
                raw={"metric": task.metadata.get("metric"), "available": False},
            )

        metric = task.metadata.get("metric")
        if metric == "startup_ms":
            measurement = measure_startup(resolved_command, task.timeout)
        elif metric == "memory_mb":
            measurement = measure_memory(resolved_command, task.timeout)
        elif metric == "binary_size_mb":
            measurement = measure_binary_size(resolved_command)
        else:
            return RunResult(
                task=task,
                status=RunStatus.FAILED,
                output="",
                error_message=f"Unsupported runtime metric: {metric}",
                raw={"metric": metric, "available": False},
            )

        return RunResult(
            task=task,
            status=measurement.status,
            output=measurement.output,
            duration_ms=measurement.duration_ms,
            peak_memory_mb=measurement.peak_memory_mb,
            exit_code=measurement.exit_code,
            error_message=measurement.error_message,
            raw=measurement.raw,
        )
