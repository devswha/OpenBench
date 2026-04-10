from __future__ import annotations

from pathlib import Path

from openbench.config import AppConfig
from openbench.metrics.store import ResultStore
from openbench.models import RunSummary
from openbench.registry import AGENT_REGISTRY, SUITE_REGISTRY
from openbench.workspace import TempWorkspaceManager


class Runner:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def run(self, agent_name: str, suite_name: str) -> RunSummary:
        if agent_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_name}")
        if suite_name not in SUITE_REGISTRY:
            raise ValueError(f"Unknown suite: {suite_name}")
        if self.config.environment_mode.value == "containerized" and suite_name != "practical":
            raise ValueError("Containerized mode is currently supported for the practical suite only")

        agent = AGENT_REGISTRY[agent_name]()
        suite = SUITE_REGISTRY[suite_name](self.config)
        store = ResultStore(self.config.results_dir)
        run_dir = store.create_run_dir()

        agent.setup()
        scores = []
        workspace_manager = TempWorkspaceManager()
        try:
            for task in suite.load_tasks():
                with workspace_manager.workspace() as workspace:
                    task.workspace = workspace
                    task.metadata["environment_mode"] = self.config.environment_mode.value
                    task.metadata["config"] = self.config
                    task.metadata["repo_root"] = str(Path(__file__).resolve().parents[1])
                    task = suite.prepare_task(task, workspace)
                    result = agent.run(task)
                    scores.append(suite.evaluate(result, agent_name))
        finally:
            agent.cleanup()

        execution_environment = {"mode": self.config.environment_mode.value}
        for score in scores:
            candidate = score.raw.get("execution_environment")
            if isinstance(candidate, dict):
                execution_environment = candidate
                break

        manifest_path = store.write_manifest(
            run_dir=run_dir,
            config=self.config,
            agent_name=agent_name,
            agent_version=agent.detect_version(),
            agent_command=agent.command,
            suite_name=suite_name,
            execution_environment=execution_environment,
        )
        suite_report_path = store.write_suite_results(
            run_dir=run_dir,
            agent_name=agent_name,
            suite_name=suite_name,
            scores=scores,
            execution_environment=execution_environment,
        )
        had_failures = any(score.status.value != "success" for score in scores)
        return RunSummary(
            run_dir=run_dir,
            manifest_path=manifest_path,
            suite_report_path=suite_report_path,
            had_failures=had_failures,
            scores=scores,
        )
