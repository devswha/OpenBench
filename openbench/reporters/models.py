from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    lower_is_better: bool = True
    description: str = ""


RUNTIME_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        key="startup_ms",
        label="Startup",
        unit="ms",
        description=(
            "Measures how quickly the agent CLI starts up and becomes responsive. "
            "Uses hyperfine to run `<command> --version` with warmup, reporting the mean "
            "execution time. Lower is better."
        ),
    ),
    MetricSpec(
        key="memory_mb",
        label="Memory",
        unit="MB",
        description=(
            "Measures peak memory consumption (Maximum Resident Set Size) during a single "
            "CLI invocation. Uses GNU time to track memory allocation. Lower is better."
        ),
    ),
    MetricSpec(
        key="binary_size_mb",
        label="Binary size",
        unit="MB",
        description=(
            "Measures the on-disk footprint of the agent CLI entry point. Uses du to "
            "calculate the resolved command path size. Lower is better."
        ),
    ),
)


@dataclass(slots=True)
class ReportMetric:
    key: str
    label: str
    unit: str
    raw_value: float | None
    normalized_score: float | None
    status: str
    available: bool
    error_message: str | None = None
    details: str | None = None

    @property
    def formatted_raw_value(self) -> str:
        if self.raw_value is None:
            return "Unavailable"

        if self.unit == "ms":
            return f"{self.raw_value:.2f} ms"
        if self.unit == "MB":
            if abs(self.raw_value) < 0.01:
                return f"{self.raw_value:.5f} MB"
            return f"{self.raw_value:.2f} MB"
        return f"{self.raw_value:.2f} {self.unit}".strip()

    @property
    def formatted_score(self) -> str:
        if self.normalized_score is None:
            return "—"
        return f"{self.normalized_score:.2f}"


@dataclass(slots=True)
class AgentReport:
    agent_name: str
    display_name: str
    metrics: list[ReportMetric] = field(default_factory=list)


@dataclass(slots=True)
class PracticalTaskResult:
    task_name: str
    description: str
    status: str
    classification: str
    score: float | None
    changed_files: list[str] = field(default_factory=list)
    touchpoint_violations: list[str] = field(default_factory=list)
    error_message: str | None = None
    duration_ms: int | None = None
    token_usage: dict[str, int | float | str | None] | None = None
    difficulty: str | None = None
    category: str | None = None
    agent_log: dict[str, int | float | str | None] | None = None

    @property
    def formatted_score(self) -> str:
        if self.score is None:
            return "—"
        return f"{self.score:.2f}"

    @property
    def formatted_duration(self) -> str:
        if self.duration_ms is None:
            return "—"
        if self.duration_ms < 1000:
            return f"{self.duration_ms} ms"
        seconds = self.duration_ms / 1000.0
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes}m {remaining:.0f}s"

    @property
    def formatted_tokens(self) -> str:
        if not self.token_usage:
            return "—"
        total = self.token_usage.get("total_tokens")
        if total is None or not isinstance(total, (int, float)):
            return "—"
        return f"{int(total):,}"


@dataclass(slots=True)
class PracticalAgentReport:
    agent_name: str
    display_name: str
    summary: dict[str, int]
    tasks: list[PracticalTaskResult] = field(default_factory=list)


@dataclass(slots=True)
class AgentDifficultyMetrics:
    """Metrics for one agent at one difficulty level."""
    agent_name: str
    difficulty: str
    task_count: int = 0
    pass_at_1: float = 0.0       # percentage
    pass_at_5: float | None = None       # percentage; None when only single-run data
    pass_at_5_strict: float | None = None  # percentage; None when only single-run data
    tokens_per_success: float | None = None
    duration_per_success: float | None = None  # in ms


@dataclass(slots=True)
class AgentCategoryMetrics:
    """Pass@1 for one agent in one category at one difficulty."""
    agent_name: str
    difficulty: str
    category: str
    pass_at_1: float = 0.0


@dataclass(slots=True)
class RuntimeReport:
    run_id: str
    suite: str
    timestamp: str
    environment: dict[str, str | int | float]
    suites: list[str] = field(default_factory=list)
    runtime_execution_environment: dict[str, str | int | float | None] = field(default_factory=dict)
    practical_execution_environment: dict[str, str | int | float | None] = field(default_factory=dict)
    agents: list[AgentReport] = field(default_factory=list)
    practical_agents: list[PracticalAgentReport] = field(default_factory=list)
    swebench_agents: list[PracticalAgentReport] = field(default_factory=list)
