from __future__ import annotations

from pathlib import Path

from openbench.config import AppConfig
from openbench.models import RunResult, RunStatus
from openbench.suites.practical.suite import PracticalTaskSuite


def test_regression_outcomes_are_classified(tmp_path: Path) -> None:
    suite = PracticalTaskSuite(AppConfig())
    task = next(task for task in suite.load_tasks() if task.name == "single-file-bug-fix")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    suite.prepare_task(task, workspace)
    task.workspace = workspace

    result = RunResult(
        task=task,
        status=RunStatus.SUCCESS,
        output="manual change",
        files_changed=["tests/test_calculator.py"],
    )

    score = suite.evaluate(result, "omc")

    assert score.status == RunStatus.REGRESSION
    assert score.raw["classification"] == "touchpoint_violation"
