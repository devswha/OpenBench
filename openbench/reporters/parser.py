from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from openbench.registry import AGENT_REGISTRY
from openbench.reporters.models import (
    AgentReport,
    PracticalAgentReport,
    PracticalTaskResult,
    ReportMetric,
    RuntimeReport,
    RUNTIME_METRICS,
)


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
    if not isinstance(suites, list):
        raise ReportInputError("Manifest suites field must be a list")

    agents = manifest.get("agents")
    if not isinstance(agents, dict) or not agents:
        raise ReportInputError("Manifest must include at least one agent entry")

    agent_reports = []
    practical_reports = []
    swebench_reports = []
    for agent_name in sorted(agents):
        runtime_json_path = input_dir / agent_name / "runtime.json"
        practical_json_path = input_dir / agent_name / "practical.json"
        swebench_json_path = input_dir / agent_name / "swe-bench.json"

        if runtime_json_path.exists():
            runtime_payload = _load_json(runtime_json_path)
            agent_reports.append(_parse_runtime_agent_report(agent_name, runtime_payload))
        elif "runtime" in suites:
            raise ReportInputError(f"Missing runtime.json for agent '{agent_name}'")

        if practical_json_path.exists():
            practical_payload = _load_json(practical_json_path)
            practical_reports.append(_parse_practical_agent_report(agent_name, practical_payload))
        elif "practical" in suites:
            raise ReportInputError(f"Missing practical.json for agent '{agent_name}'")

        if swebench_json_path.exists():
            swebench_payload = _load_json(swebench_json_path)
            swebench_reports.append(_parse_practical_agent_report(agent_name, swebench_payload, suite_name="swe-bench"))
        elif "swe-bench" in suites:
            raise ReportInputError(f"Missing swe-bench.json for agent '{agent_name}'")

    if not agent_reports and not practical_reports and not swebench_reports:
        raise ReportInputError("Input run does not contain any supported suite artifacts")

    report = RuntimeReport(
        run_id=input_dir.name,
        suite="runtime" if agent_reports else "practical",
        timestamp=str(manifest.get("timestamp", "")),
        environment=dict(manifest.get("environment", {})),
        suites=[suite for suite in suites if isinstance(suite, str)],
        runtime_execution_environment=_first_execution_environment(agent_reports, "runtime", input_dir),
        practical_execution_environment=_first_execution_environment(practical_reports, "practical", input_dir),
        agents=agent_reports,
        practical_agents=practical_reports,
        swebench_agents=swebench_reports,
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


def _parse_runtime_agent_report(agent_name: str, payload: dict[str, Any]) -> AgentReport:
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


def _parse_practical_agent_report(
    agent_name: str,
    payload: dict[str, Any],
    suite_name: str = "practical",
) -> PracticalAgentReport:
    suite = payload.get("suite")
    if suite != suite_name:
        raise ReportInputError(f"Expected {suite_name} suite payload for agent '{agent_name}', got {suite!r}")

    task_entries = payload.get("tasks")
    if not isinstance(task_entries, list):
        raise ReportInputError(f"Expected a task list in practical payload for agent '{agent_name}'")

    tasks: list[PracticalTaskResult] = []
    for task_entry in task_entries:
        raw = task_entry.get("raw")
        if not isinstance(raw, dict):
            raise ReportInputError(f"Practical task entry for agent '{agent_name}' is missing raw data")
        raw_duration = raw.get("duration_ms")
        raw_token_usage = raw.get("token_usage")
        tasks.append(
            PracticalTaskResult(
                task_name=str(task_entry.get("task_name", "")),
                description=str(raw.get("description", "")),
                status=str(task_entry.get("status", "unknown")),
                classification=str(raw.get("classification", "unknown")),
                score=float(task_entry["value"]) if isinstance(task_entry.get("value"), (int, float)) else None,
                changed_files=list(raw.get("changed_files", [])),
                touchpoint_violations=list(raw.get("touchpoint_violations", [])),
                error_message=_optional_str(raw.get("agent_error_message")),
                duration_ms=int(raw_duration) if isinstance(raw_duration, (int, float)) else None,
                token_usage=dict(raw_token_usage) if isinstance(raw_token_usage, dict) else None,
                difficulty=_optional_str(raw.get("difficulty")),
                category=_optional_str(raw.get("category")),
                agent_log=dict(raw["agent_log"]) if isinstance(raw.get("agent_log"), dict) else None,
            )
        )

    agent_factory = AGENT_REGISTRY.get(agent_name)
    display_name = agent_name
    if agent_factory is not None:
        display_name = getattr(agent_factory, "display_name", agent_name)

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ReportInputError(f"Practical payload for agent '{agent_name}' is missing summary")

    return PracticalAgentReport(
        agent_name=agent_name,
        display_name=display_name,
        summary={
            "task_count": int(summary.get("task_count", 0)),
            "successful_tasks": int(summary.get("successful_tasks", 0)),
            "failed_tasks": int(summary.get("failed_tasks", 0)),
        },
        tasks=tasks,
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _first_execution_environment(items: list[Any], suite_name: str, input_dir: Path) -> dict[str, Any]:
    if not items:
        return {}
    agent_name = items[0].agent_name
    suite_path = input_dir / agent_name / f"{suite_name}.json"
    payload = _load_json(suite_path)
    environment = payload.get("execution_environment", {})
    return dict(environment) if isinstance(environment, dict) else {}
