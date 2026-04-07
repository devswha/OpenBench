from __future__ import annotations

from openbench.config import AppConfig
from openbench.suites.practical.suite import PracticalTaskSuite


def test_practical_suite_loads_five_frozen_tasks() -> None:
    suite = PracticalTaskSuite(AppConfig())

    tasks = suite.load_tasks()

    assert len(tasks) == 5
    assert [task.name for task in tasks] == [
        "single-file-bug-fix",
        "failing-unit-test-repair",
        "config-schema-migration",
        "multi-file-import-repair",
        "validation-error-handling-patch",
    ]
    assert all(task.metadata["task_kind"] == "practical" for task in tasks)

