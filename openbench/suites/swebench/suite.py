"""SWE-bench Verified benchmark suite."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from openbench.models import DoctorCheck, RunResult, RunStatus, Score, Task
from openbench.suites.base import BenchSuite
from openbench.suites.swebench.docker import (
    ensure_image,
    image_name_for_instance,
    run_tests_in_container,
)
from openbench.suites.swebench.evaluation import (
    check_tests_passed,
    determine_test_command,
    parse_fail_to_pass,
)
from openbench.suites.swebench.repo import apply_patch, clone_and_checkout


class SweBenchSuite(BenchSuite):
    name = "swe-bench"
    tier = 2
    description = "SWE-bench Verified subset: real GitHub issues"

    def definition_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "tasks" / "swe-bench" / "suite.yaml"

    def instances_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "tasks" / "swe-bench" / "instances.json"

    def load_tasks(self) -> list[Task]:
        suite_data = yaml.safe_load(self.definition_path().read_text())
        if not isinstance(suite_data, dict) or not isinstance(suite_data.get("instances"), list):
            raise ValueError("SWE-bench suite definition must contain an 'instances' list")

        instances_path = self.instances_path()
        if not instances_path.exists():
            raise ValueError(
                f"SWE-bench instances not found at {instances_path}. "
                "Run 'openbench fetch swe-bench' to download the dataset."
            )

        all_instances = json.loads(instances_path.read_text())
        instance_map = {inst["instance_id"]: inst for inst in all_instances}

        defaults = suite_data.get("defaults", {})
        default_timeout = int(defaults.get("timeout", 600))

        tasks: list[Task] = []
        for entry in suite_data["instances"]:
            instance_id = str(entry["id"])
            if instance_id not in instance_map:
                raise ValueError(f"Instance '{instance_id}' not found in instances.json")

            instance = instance_map[instance_id]
            difficulty = str(entry.get("difficulty", "medium"))
            category = str(entry.get("category", "bugfix"))
            timeout = int(entry.get("timeout", default_timeout))

            tasks.append(Task(
                name=instance_id,
                prompt=instance["problem_statement"],
                timeout=timeout,
                metadata={
                    "task_kind": "practical",
                    "description": instance["problem_statement"][:200],
                    "swebench_instance": instance,
                    "difficulty": difficulty,
                    "category": category,
                },
            ))
        return tasks

    def prepare_task(self, task: Task, workspace: Path) -> Task:
        instance = task.metadata["swebench_instance"]
        clone_and_checkout(
            repo=instance["repo"],
            base_commit=instance["base_commit"],
            workspace=workspace,
            timeout=300,
        )
        # Pre-pull Docker image (so it's cached for evaluation)
        try:
            ensure_image(instance)
        except RuntimeError:
            pass  # Docker pull failure is non-fatal during preparation
        return task

    def evaluate(self, result: RunResult, agent_name: str) -> Score:
        instance = result.task.metadata["swebench_instance"]
        difficulty = result.task.metadata.get("difficulty", "medium")
        category = result.task.metadata.get("category", "bugfix")

        if result.status != RunStatus.SUCCESS:
            return Score(
                task_name=result.task.name,
                agent_name=agent_name,
                value=0.0,
                raw={
                    "task_kind": "swe-bench",
                    "description": result.task.metadata.get("description", ""),
                    "difficulty": difficulty,
                    "category": category,
                    "classification": "agent_error",
                    "error_message": result.error_message,
                    "duration_ms": result.duration_ms,
                },
                tier=self.tier,
                status=result.status,
            )

        # Apply test patch
        test_patch = instance.get("test_patch", "")
        try:
            if test_patch:
                apply_patch(
                    workspace=result.task.workspace,
                    patch_content=test_patch,
                )
        except RuntimeError as exc:
            return Score(
                task_name=result.task.name,
                agent_name=agent_name,
                value=0.0,
                raw={
                    "task_kind": "swe-bench",
                    "description": result.task.metadata.get("description", ""),
                    "difficulty": difficulty,
                    "category": category,
                    "classification": "patch_error",
                    "error_message": str(exc),
                    "duration_ms": result.duration_ms,
                },
                tier=self.tier,
                status=RunStatus.FAILED,
            )

        # Run tests in Docker container
        image = image_name_for_instance(instance)
        test_command = determine_test_command(instance)
        fail_to_pass = parse_fail_to_pass(instance)

        try:
            test_output = run_tests_in_container(
                image=image,
                workspace=result.task.workspace,
                test_command=test_command,
                timeout=result.task.timeout,
            )
        except RuntimeError as exc:
            return Score(
                task_name=result.task.name,
                agent_name=agent_name,
                value=0.0,
                raw={
                    "task_kind": "swe-bench",
                    "description": result.task.metadata.get("description", ""),
                    "difficulty": difficulty,
                    "category": category,
                    "classification": "test_error",
                    "error_message": str(exc),
                    "duration_ms": result.duration_ms,
                },
                tier=self.tier,
                status=RunStatus.FAILED,
            )

        passed = check_tests_passed(test_output, fail_to_pass)
        classification = "pass" if passed else "fail"
        final_status = RunStatus.SUCCESS if passed else RunStatus.FAILED

        raw: dict[str, object] = {
            "task_kind": "swe-bench",
            "description": result.task.metadata.get("description", ""),
            "difficulty": difficulty,
            "category": category,
            "classification": classification,
            "instance_id": instance["instance_id"],
            "repo": instance["repo"],
            "changed_files": result.files_changed,
            "test_output": test_output[:2000],  # Truncate for storage
            "fail_to_pass": fail_to_pass,
            "fail_to_pass_resolved": passed,
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
        agent_log = result.raw.get("agent_log")
        if agent_log is not None:
            raw["agent_log"] = agent_log

        return Score(
            task_name=result.task.name,
            agent_name=agent_name,
            value=100.0 if passed else 0.0,
            raw=raw,
            tier=self.tier,
            status=final_status,
        )

    def doctor_checks(self) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []
        # Check instances.json
        instances_path = self.instances_path()
        checks.append(DoctorCheck(
            name="swe-bench instances",
            ok=instances_path.exists(),
            details=str(instances_path) if instances_path.exists() else "missing — run 'openbench fetch swe-bench'",
            category="swe-bench",
        ))
        # Check Docker
        docker_bin = shutil.which("docker")
        checks.append(DoctorCheck(
            name="swe-bench docker",
            ok=docker_bin is not None,
            details=docker_bin or "docker not found",
            category="swe-bench",
        ))
        # Check git
        git_bin = shutil.which("git")
        checks.append(DoctorCheck(
            name="swe-bench git",
            ok=git_bin is not None,
            details=git_bin or "git not found",
            category="swe-bench",
        ))
        return checks
