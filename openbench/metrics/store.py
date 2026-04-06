from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
from typing import Any

from openbench.config import AppConfig
from openbench.models import Score


class ResultStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def create_run_dir(self) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
        run_dir = self.root_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir

    def write_manifest(
        self,
        *,
        run_dir: Path,
        config: AppConfig,
        agent_name: str,
        agent_version: str,
        agent_command: str,
        suite_name: str,
    ) -> Path:
        manifest = {
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {
                agent_name: {
                    "version": agent_version,
                    "command": agent_command,
                }
            },
            "suites": [suite_name],
            "normalization_references": {
                "startup_ms": config.normalization.startup_ms,
                "memory_mb": config.normalization.memory_mb,
                "binary_size_mb": config.normalization.binary_size_mb,
            },
            "environment": self._environment_info(),
        }
        manifest_path = run_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return manifest_path

    def write_suite_results(self, *, run_dir: Path, agent_name: str, suite_name: str, scores: list[Score]) -> Path:
        agent_dir = run_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "suite": suite_name,
            "agent": agent_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [self._serialize(score) for score in scores],
            "summary": {
                "task_count": len(scores),
                "successful_tasks": sum(score.status.value == "success" for score in scores),
                "failed_tasks": sum(score.status.value != "success" for score in scores),
            },
        }
        report_path = agent_dir / f"{suite_name}.json"
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        return report_path

    def _environment_info(self) -> dict[str, Any]:
        info = {
            "os": platform.platform(),
            "python": platform.python_version(),
            "cpu": platform.processor() or platform.machine(),
        }
        memory_gb = self._memory_gb()
        if memory_gb is not None:
            info["memory_gb"] = memory_gb
        return info

    def _memory_gb(self) -> float | None:
        if not hasattr(os, "sysconf"):
            return None
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            page_count = os.sysconf("SC_PHYS_PAGES")
        except (ValueError, OSError, AttributeError):
            return None
        return round((page_size * page_count) / (1024**3), 2)

    def _serialize(self, value: Any) -> Any:
        if is_dataclass(value):
            return self._serialize(asdict(value))
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {key: self._serialize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._serialize(item) for item in value]
        if hasattr(value, "value") and not isinstance(value, (str, bytes)):
            enum_value = getattr(value, "value", None)
            if isinstance(enum_value, (str, int, float, bool)) or enum_value is None:
                return enum_value
        return value
