from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EnvironmentMode(str, Enum):
    NATIVE = "native"
    CONTAINERIZED = "containerized"


class RunStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    REGRESSION = "regression"
    TIMEOUT = "timeout"
    OOM = "oom"
    CRASH = "crash"
    SETUP_ERROR = "setup_error"


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None = None
    provider: str = "unknown"


@dataclass(slots=True)
class Task:
    name: str
    prompt: str = ""
    workspace: Path = field(default_factory=lambda: Path("."))
    timeout: int = 30
    expected: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionEnvironment:
    mode: EnvironmentMode = EnvironmentMode.NATIVE
    base_image: str | None = None
    base_image_id: str | None = None
    agent_image: str | None = None
    agent_image_id: str | None = None
    setup_overhead_ms: int = 0
    cache_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunResult:
    task: Task
    status: RunStatus
    output: str = ""
    duration_ms: int = 0
    peak_memory_mb: float | None = None
    token_usage: TokenUsage | None = None
    files_changed: list[str] = field(default_factory=list)
    exit_code: int = 0
    error_message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Score:
    task_name: str
    agent_name: str
    value: float | None
    raw: dict[str, Any]
    tier: int
    status: RunStatus


@dataclass(slots=True)
class DoctorCheck:
    name: str
    ok: bool
    details: str
    category: str = "general"


@dataclass(slots=True)
class RunSummary:
    run_dir: Path
    manifest_path: Path
    suite_report_path: Path
    had_failures: bool
    scores: list[Score]
