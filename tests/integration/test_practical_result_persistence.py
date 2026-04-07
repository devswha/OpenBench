from __future__ import annotations

import json

from openbench.config import load_config
from openbench.runner import Runner


def test_task_results_are_persisted(shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run("omc", "practical")

    payload = json.loads(summary.suite_report_path.read_text())
    task = payload["tasks"][0]
    assert task["raw"]["task_kind"] == "practical"
    assert "classification" in task["raw"]
    assert "changed_files" in task["raw"]
    assert "success_command" in task["raw"]

