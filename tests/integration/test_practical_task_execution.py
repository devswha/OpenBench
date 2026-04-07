from __future__ import annotations

import json

import pytest

from openbench.config import load_config
from openbench.runner import Runner


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_practical_task_suite_executes(agent_name: str, shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run(agent_name, "practical")

    assert summary.had_failures is False
    payload = json.loads(summary.suite_report_path.read_text())
    assert payload["suite"] == "practical"
    assert payload["summary"]["task_count"] == 5
    assert payload["summary"]["failed_tasks"] == 0

