from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shlex
import shutil
from typing import Any

import yaml

from openbench.containerization import ContainerizedExecutionError, run_check_in_container
from openbench.models import RunResult, RunStatus, Score, Task
from openbench.suites.base import BenchSuite
from openbench.suites.practical.contracts import PracticalTaskContract
from openbench.utils.process import combine_output, run_subprocess


class PracticalTaskSuite(BenchSuite):
    name = "practical"
    tier = 1
    description = "Deterministic practical coding tasks on frozen in-repo fixtures"

    def definition_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "tasks" / "practical" / "suite.yaml"

    def load_tasks(self) -> list[Task]:
        data = yaml.safe_load(self.definition_path().read_text())
        if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
            raise ValueError("Practical suite definition must contain a top-level 'tasks' list")

        tasks: list[Task] = []
        for raw_task in data["tasks"]:
            contract = self._validate_contract(raw_task)
            prompt = self._build_prompt(contract)
            tasks.append(
                Task(
                    name=contract.identifier,
                    prompt=prompt,
                    timeout=contract.timeout,
                    expected={
                        "success_command": contract.success_command,
                        "regression_command": contract.regression_command,
                    },
                    metadata={
                        "task_kind": "practical",
                        "description": contract.description,
                        "fixture": str(contract.fixture),
                        "allowed_touchpoints": contract.allowed_touchpoints,
                        "success_command": contract.success_command,
                        "regression_command": contract.regression_command,
                        "contract": asdict(contract),
                    },
                )
            )
        return tasks

    def prepare_task(self, task: Task, workspace: Path) -> Task:
        fixture = Path(task.metadata["fixture"])
        workspace_src = fixture / "workspace"
        if workspace_src.exists():
            shutil.copytree(workspace_src, workspace, dirs_exist_ok=True)
        else:
            # Backward compat: if no workspace/ subdir, copy everything
            shutil.copytree(fixture, workspace, dirs_exist_ok=True)
        return task

    def evaluate(self, result: RunResult, agent_name: str) -> Score:
        success_command = str(result.task.metadata["success_command"])
        regression_command = str(result.task.metadata["regression_command"])
        allowed_touchpoints = set(result.task.metadata["allowed_touchpoints"])
        execution_environment = result.raw.get(
            "execution_environment",
            {"mode": result.task.metadata.get("environment_mode", "native")},
        )

        touchpoint_violations = [
            changed for changed in result.files_changed if changed not in allowed_touchpoints
        ]

        if result.status != RunStatus.SUCCESS:
            error_raw: dict[str, object] = {
                "task_kind": "practical",
                "classification": "agent_error",
                "changed_files": result.files_changed,
                "touchpoint_violations": touchpoint_violations,
                "error_message": result.error_message,
                "output": result.output,
                "execution_environment": execution_environment,
                "duration_ms": result.duration_ms,
            }
            if result.token_usage is not None:
                error_raw["token_usage"] = {
                    "input_tokens": result.token_usage.input_tokens,
                    "output_tokens": result.token_usage.output_tokens,
                    "total_tokens": result.token_usage.total_tokens,
                    "estimated_cost_usd": result.token_usage.estimated_cost_usd,
                    "provider": result.token_usage.provider,
                }
            return Score(
                task_name=result.task.name,
                agent_name=agent_name,
                value=0.0,
                raw=error_raw,
                tier=self.tier,
                status=result.status,
            )

        # Copy evaluation files (hidden tests) into workspace for verification
        fixture = Path(result.task.metadata["fixture"])
        evaluation_src = fixture / "evaluation"
        if evaluation_src.exists():
            shutil.copytree(evaluation_src, result.task.workspace, dirs_exist_ok=True)

        if execution_environment.get("mode") == "containerized":
            try:
                success_check = run_check_in_container(
                    execution_environment=result.raw["execution_environment_contract"],
                    command=shlex.split(success_command),
                    workspace=result.task.workspace,
                    timeout=result.task.timeout,
                )
                regression_check = run_check_in_container(
                    execution_environment=result.raw["execution_environment_contract"],
                    command=shlex.split(regression_command),
                    workspace=result.task.workspace,
                    timeout=result.task.timeout,
                )
            except ContainerizedExecutionError as exc:
                return Score(
                    task_name=result.task.name,
                    agent_name=agent_name,
                    value=0.0,
                    raw={
                        "task_kind": "practical",
                        "classification": "container_error",
                        "changed_files": result.files_changed,
                        "touchpoint_violations": touchpoint_violations,
                        "error_message": str(exc),
                        "execution_environment": execution_environment,
                    },
                    tier=self.tier,
                    status=RunStatus.SETUP_ERROR,
                )
        else:
            success_check = run_subprocess(
                shlex.split(success_command), cwd=result.task.workspace, timeout=result.task.timeout
            )
            regression_check = run_subprocess(
                shlex.split(regression_command), cwd=result.task.workspace, timeout=result.task.timeout
            )

        classification = "pass"
        final_status = RunStatus.SUCCESS
        if touchpoint_violations:
            classification = "touchpoint_violation"
            final_status = RunStatus.REGRESSION
        elif success_check.returncode != 0:
            classification = "task_failure"
            final_status = RunStatus.FAILED
        elif regression_check.returncode != 0:
            classification = "regression"
            final_status = RunStatus.REGRESSION

        raw: dict[str, object] = {
            "task_kind": "practical",
            "description": result.task.metadata["description"],
            "classification": classification,
            "changed_files": result.files_changed,
            "touchpoint_violations": touchpoint_violations,
            "allowed_touchpoints": sorted(allowed_touchpoints),
            "success_command": success_command,
            "success_command_exit_code": success_check.returncode,
            "success_command_output": combine_output(success_check),
            "regression_command": regression_command,
            "regression_command_exit_code": regression_check.returncode,
            "regression_command_output": combine_output(regression_check),
            "execution_environment": execution_environment,
            "duration_ms": result.duration_ms,
        }
        if result.token_usage is not None:
            raw["token_usage"] = {
                "input_tokens": result.token_usage.input_tokens,
                "output_tokens": result.token_usage.output_tokens,
                "total_tokens": result.token_usage.total_tokens,
                "estimated_cost_usd": result.token_usage.estimated_cost_usd,
                "provider": result.token_usage.provider,
            }
        if result.error_message:
            raw["agent_error_message"] = result.error_message
        if result.output:
            raw["agent_output"] = result.output

        return Score(
            task_name=result.task.name,
            agent_name=agent_name,
            value=100.0 if final_status == RunStatus.SUCCESS else 0.0,
            raw=raw,
            tier=self.tier,
            status=final_status,
        )

    def _validate_contract(self, raw_task: dict[str, Any]) -> PracticalTaskContract:
        required = {
            "id",
            "description",
            "fixture",
            "allowed_touchpoints",
            "success_command",
            "regression_command",
            "timeout",
        }
        missing = sorted(required - raw_task.keys())
        if missing:
            raise ValueError(f"Practical task is missing keys: {', '.join(missing)}")

        allowed_touchpoints = raw_task["allowed_touchpoints"]
        if not isinstance(allowed_touchpoints, list) or not all(
            isinstance(item, str) for item in allowed_touchpoints
        ):
            raise ValueError("allowed_touchpoints must be a list of relative file paths")

        fixture = self.definition_path().parent / "fixtures" / str(raw_task["fixture"])
        if not fixture.exists():
            raise ValueError(f"Fixture directory does not exist: {fixture}")

        return PracticalTaskContract(
            identifier=str(raw_task["id"]),
            description=str(raw_task["description"]),
            fixture=fixture,
            allowed_touchpoints=list(allowed_touchpoints),
            success_command=str(raw_task["success_command"]),
            regression_command=str(raw_task["regression_command"]),
            timeout=int(raw_task["timeout"]),
        )

    def _build_prompt(self, contract: PracticalTaskContract) -> str:
        allowed = ", ".join(contract.allowed_touchpoints)
        return (
            "You are given a project in the current working directory.\n"
            "\n"
            f"## Task\n"
            f"{contract.description}\n"
            "\n"
            f"## Editable files\n"
            f"{allowed}\n"
            "\n"
            "## Constraints\n"
            "- Only modify files listed as editable above\n"
            "- Do not install additional packages\n"
            "- Your changes will be validated by automated tests (not shown)\n"
        )
