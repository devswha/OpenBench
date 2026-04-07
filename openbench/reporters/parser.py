from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from openbench.registry import AGENT_REGISTRY
from openbench.reporters.models import AgentReport, ReportMetric, RuntimeReport, RUNTIME_METRICS


class ReportInputError(ValueError):
    """Raised when a saved run directory cannot be parsed into a stable report contract."""


@dataclass(frozen=True, slots=True)
class ParsedRun:
    report: RuntimeReport
    input_dir: Path


def parse_runtime_report(input_dir: Path) -> ParsedRun:
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.exists():
        raise ReportInputError(f"Missing manifest.json in {input_dir}")

    manifest = _load_json(manifest_path)
    suites = manifest.get("suites", [])
    if not isinstance(suites, list) or "runtime" not in suites:
        raise ReportInputError("Input run does not declare the runtime suite")

    agents = manifest.get("agents")
    if not isinstance(agents, dict) or not agents:
        raise ReportInputError("Manifest must include at least one agent entry")

    agent_reports = []
    for agent_name in sorted(agents):
        runtime_json_path = input_dir / agent_name / "runtime.json"
        if not runtime_json_path.exists():
            raise ReportInputError(f"Missing runtime.json for agent '{agent_name}'")
        runtime_payload = _load_json(runtime_json_path)
        agent_reports.append(_parse_agent_report(agent_name, runtime_payload))

    report = RuntimeReport(
        run_id=input_dir.name,
        suite="runtime",
        timestamp=str(manifest.get("timestamp", "")),
        environment=dict(manifest.get("environment", {})),
        agents=agent_reports,
    )
    return ParsedRun(report=report, input_dir=input_dir)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ReportInputError(f"Malformed JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ReportInputError(f"Expected top-level object in {path}")
    return payload


def _parse_agent_report(agent_name: str, payload: dict[str, Any]) -> AgentReport:
    suite = payload.get("suite")
    if suite != "runtime":
        raise ReportInputError(f"Expected runtime suite payload for agent '{agent_name}', got {suite!r}")

    task_entries = payload.get("tasks")
    if not isinstance(task_entries, list):
        raise ReportInputError(f"Expected a task list in runtime payload for agent '{agent_name}'")

    tasks_by_metric: dict[str, dict[str, Any]] = {}
    for task_entry in task_entries:
        raw = task_entry.get("raw")
        if not isinstance(raw, dict):
            raise ReportInputError(f"Task entry for agent '{agent_name}' is missing raw metric data")
        metric_key = raw.get("metric")
        if not isinstance(metric_key, str):
            raise ReportInputError(f"Task entry for agent '{agent_name}' is missing a metric key")
        tasks_by_metric[metric_key] = task_entry

    metrics: list[ReportMetric] = []
    for metric_spec in RUNTIME_METRICS:
        if metric_spec.key not in tasks_by_metric:
            raise ReportInputError(
                f"Agent '{agent_name}' runtime payload is missing metric '{metric_spec.key}'"
            )

        task_entry = tasks_by_metric[metric_spec.key]
        raw = task_entry["raw"]
        raw_value = raw.get("value")
        normalized_score = task_entry.get("value")
        metrics.append(
            ReportMetric(
                key=metric_spec.key,
                label=metric_spec.label,
                unit=metric_spec.unit,
                raw_value=float(raw_value) if isinstance(raw_value, (int, float)) else None,
                normalized_score=(
                    float(normalized_score) if isinstance(normalized_score, (int, float)) else None
                ),
                status=str(task_entry.get("status", "unknown")),
                available=bool(raw.get("available", False)),
                error_message=_optional_str(raw.get("error_message")),
                details=_optional_str(raw.get("output")),
            )
        )

    agent_factory = AGENT_REGISTRY.get(agent_name)
    display_name = agent_name
    if agent_factory is not None:
        display_name = getattr(agent_factory, "display_name", agent_name)

    return AgentReport(agent_name=agent_name, display_name=display_name, metrics=metrics)


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None

