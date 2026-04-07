from __future__ import annotations

from openbench.config import AppConfig
from openbench.suites.practical.suite import PracticalTaskSuite


def test_practical_tasks_expose_explicit_contract_fields() -> None:
    suite = PracticalTaskSuite(AppConfig())

    tasks = suite.load_tasks()

    for task in tasks:
        contract = task.metadata["contract"]
        assert contract["identifier"] == task.name
        assert contract["allowed_touchpoints"]
        assert contract["success_command"]
        assert contract["regression_command"]

