from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time

from openbench.containerization import (
    ContainerizedExecutionError,
    ensure_practical_images,
    execution_environment_payload,
    run_in_container,
)
from openbench.models import DoctorCheck, RunResult, RunStatus, Task
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
        self._execution_environment_cache: dict[str, object] = {}

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
        task_kind = str(task.metadata.get("task_kind", "runtime"))
        if task_kind == "practical":
            return self.run_practical_task(task)

        resolved_command = self.resolve_command()
        if resolved_command is None:
            return self._missing_command_result(
                task,
                {"metric": task.metadata.get("metric"), "available": False},
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
            raw={
                **measurement.raw,
                "execution_environment": {"mode": task.metadata.get("environment_mode", "native")},
            },
        )

    def build_practical_command(self, resolved_command: str, task: Task) -> list[str]:
        raise NotImplementedError

    def run_practical_task(self, task: Task) -> RunResult:
        resolved_command = self.resolve_command()
        if resolved_command is None:
            return self._missing_command_result(task, {"task_kind": "practical", "available": False})

        before = self._snapshot_workspace(task.workspace)
        environment_mode = str(task.metadata.get("environment_mode", "native"))
        started = time.perf_counter()
        try:
            execution_environment_contract = None
            if environment_mode == "containerized":
                cache_key = f"{environment_mode}:{self.name}"
                cached = self._execution_environment_cache.get(cache_key)
                if cached is None:
                    cached = ensure_practical_images(
                        task.metadata["config"],
                        self.name,
                        repo_root=Path(task.metadata["repo_root"]),
                    )
                    self._execution_environment_cache[cache_key] = cached
                execution_environment_contract = cached
                completed = run_in_container(
                    execution_environment=execution_environment_contract,
                    command=self.build_practical_command(self.command, task),
                    workspace=task.workspace,
                    timeout=task.timeout,
                )
            else:
                completed = run_subprocess(
                    self.build_practical_command(resolved_command, task),
                    timeout=task.timeout,
                    cwd=task.workspace,
                )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.perf_counter() - started) * 1000)
            after = self._snapshot_workspace(task.workspace)
            return RunResult(
                task=task,
                status=RunStatus.TIMEOUT,
                output="",
                duration_ms=duration_ms,
                error_message=f"Task timed out after {task.timeout}s",
                files_changed=self._diff_workspace(before, after),
                raw={"task_kind": "practical", "available": False},
            )
        except ContainerizedExecutionError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            after = self._snapshot_workspace(task.workspace)
            return RunResult(
                task=task,
                status=RunStatus.SETUP_ERROR,
                output="",
                duration_ms=duration_ms,
                error_message=str(exc),
                files_changed=self._diff_workspace(before, after),
                raw={
                    "task_kind": "practical",
                    "available": False,
                    "execution_environment": {"mode": "containerized"},
                },
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        after = self._snapshot_workspace(task.workspace)
        status = RunStatus.SUCCESS if completed.returncode == 0 else RunStatus.FAILED
        execution_environment = (
            execution_environment_payload(execution_environment_contract)
            if environment_mode == "containerized"
            else {"mode": "native"}
        )
        return RunResult(
            task=task,
            status=status,
            output=combine_output(completed),
            duration_ms=duration_ms,
            exit_code=completed.returncode,
            error_message=None if completed.returncode == 0 else "Agent command failed",
            files_changed=self._diff_workspace(before, after),
            raw={
                "task_kind": "practical",
                "available": True,
                "execution_environment": execution_environment,
                "execution_environment_contract": execution_environment_contract,
            },
        )

    def _snapshot_workspace(self, workspace: Path) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for path in workspace.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            relative = path.relative_to(workspace).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[relative] = digest
        return snapshot

    def _diff_workspace(self, before: dict[str, str], after: dict[str, str]) -> list[str]:
        changed = []
        for relative in sorted(set(before) | set(after)):
            if before.get(relative) != after.get(relative):
                changed.append(relative)
        return changed

    def _missing_command_result(self, task: Task, raw: dict[str, object]) -> RunResult:
        return RunResult(
            task=task,
            status=RunStatus.SETUP_ERROR,
            output="",
            error_message=f"Agent command '{self.command}' is not available",
            raw=raw,
        )
