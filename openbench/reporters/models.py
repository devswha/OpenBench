from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    lower_is_better: bool = True


RUNTIME_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(key="startup_ms", label="Startup", unit="ms"),
    MetricSpec(key="memory_mb", label="Memory", unit="MB"),
    MetricSpec(key="binary_size_mb", label="Binary size", unit="MB"),
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
class RuntimeReport:
    run_id: str
    suite: str
    timestamp: str
    environment: dict[str, str | int | float]
    agents: list[AgentReport] = field(default_factory=list)
