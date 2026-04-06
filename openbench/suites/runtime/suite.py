from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

from openbench.models import RunResult, Score, Task
from openbench.suites.base import BenchSuite
from openbench.suites.runtime.measurements import doctor_checks as runtime_doctor_checks


class RuntimeSuite(BenchSuite):
    name = "runtime"
    tier = 0
    description = "Startup, memory, and binary-size measurements for agent CLIs"

    def definition_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "tasks" / "runtime" / "suite.yaml"

    def load_tasks(self) -> list[Task]:
        data = yaml.safe_load(self.definition_path().read_text())
        if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
            raise ValueError("Runtime suite definition must contain a top-level 'tasks' list")

        tasks: list[Task] = []
        for raw_task in data["tasks"]:
            tasks.append(self._validate_task(raw_task))
        return tasks

    def _validate_task(self, raw_task: dict[str, Any]) -> Task:
        required_keys = {"name", "timeout", "metadata"}
        missing = sorted(required_keys - raw_task.keys())
        if missing:
            raise ValueError(f"Runtime task is missing keys: {', '.join(missing)}")

        metadata = raw_task["metadata"]
        if not isinstance(metadata, dict) or "metric" not in metadata:
            raise ValueError("Runtime task metadata must include 'metric'")

        return Task(
            name=str(raw_task["name"]),
            prompt=str(raw_task.get("prompt", "")),
            timeout=int(raw_task["timeout"]),
            expected=dict(raw_task.get("expected", {})),
            metadata=dict(metadata),
        )

    def evaluate(self, result: RunResult, agent_name: str) -> Score:
        metric = str(result.raw.get("metric", result.task.metadata.get("metric", result.task.name)))
        actual_value = result.raw.get("value")
        normalized_score = None
        if isinstance(actual_value, (int, float)):
            normalized_score = self._normalize_metric(metric, float(actual_value))

        raw = {
            **result.raw,
            "task_name": result.task.name,
            "status": result.status.value,
            "exit_code": result.exit_code,
            "error_message": result.error_message,
        }
        if result.peak_memory_mb is not None:
            raw["peak_memory_mb"] = result.peak_memory_mb
        if result.output:
            raw["output"] = result.output

        return Score(
            task_name=result.task.name,
            agent_name=agent_name,
            value=normalized_score,
            raw=raw,
            tier=self.tier,
            status=result.status,
        )

    def doctor_checks(self):
        return runtime_doctor_checks()

    def _normalize_metric(self, metric: str, value: float) -> float:
        if value <= 0:
            return 100.0

        if metric == "startup_ms":
            reference = self.config.normalization.startup_ms
        elif metric == "memory_mb":
            reference = self.config.normalization.memory_mb
        elif metric == "binary_size_mb":
            reference = self.config.normalization.binary_size_mb
        else:
            return 0.0

        ratio = reference / value
        score = 50.0 + 50.0 * math.log2(ratio) / math.log2(10)
        return max(0.0, min(100.0, score))
