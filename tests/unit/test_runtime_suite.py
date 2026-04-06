from __future__ import annotations

from openbench.config import AppConfig
from openbench.models import RunResult, RunStatus, Task
from openbench.suites.runtime.suite import RuntimeSuite


def test_runtime_suite_loads_yaml_tasks() -> None:
    suite = RuntimeSuite(AppConfig())

    tasks = suite.load_tasks()

    assert [task.name for task in tasks] == ["startup", "memory", "binary-size"]


def test_runtime_suite_evaluates_successful_result() -> None:
    suite = RuntimeSuite(AppConfig())
    task = Task(name="startup", metadata={"metric": "startup_ms"})
    result = RunResult(task=task, status=RunStatus.SUCCESS, raw={"metric": "startup_ms", "value": 250.0})

    score = suite.evaluate(result, "omc")

    assert score.task_name == "startup"
    assert score.agent_name == "omc"
    assert score.value is not None
