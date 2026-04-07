from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shlex
import shutil
from typing import Any

import yaml

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
        shutil.copytree(fixture, workspace, dirs_exist_ok=True)
        return task

    def evaluate(self, result: RunResult, agent_name: str) -> Score:
        success_command = str(result.task.metadata["success_command"])
        regression_command = str(result.task.metadata["regression_command"])
        allowed_touchpoints = set(result.task.metadata["allowed_touchpoints"])

        touchpoint_violations = [
            changed for changed in result.files_changed if changed not in allowed_touchpoints
        ]

        if result.status != RunStatus.SUCCESS:
            return Score(
                task_name=result.task.name,
                agent_name=agent_name,
                value=0.0,
                raw={
                    "task_kind": "practical",
                    "classification": "agent_error",
                    "changed_files": result.files_changed,
                    "touchpoint_violations": touchpoint_violations,
                    "error_message": result.error_message,
                    "output": result.output,
                },
                tier=self.tier,
                status=result.status,
            )

        success_check = run_subprocess(shlex.split(success_command), cwd=result.task.workspace, timeout=result.task.timeout)
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

        raw = {
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
            "You are working inside the current fixture repository.\n"
            f"Task ID: {contract.identifier}\n"
            f"Task: {contract.description}\n"
            f"Allowed touchpoints: {allowed}\n"
            "Make the minimum code changes needed to satisfy the task.\n"
            "Do not edit files outside the allowed touchpoints.\n"
            f"Primary success check: {contract.success_command}\n"
            f"Regression check: {contract.regression_command}\n"
        )
