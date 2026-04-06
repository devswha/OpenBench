from __future__ import annotations

import json

from openbench.config import AppConfig
from openbench.metrics.store import ResultStore
from openbench.models import RunStatus, Score


def test_manifest_contains_required_metadata(tmp_path) -> None:
    store = ResultStore(tmp_path)
    run_dir = store.create_run_dir()

    manifest_path = store.write_manifest(
        run_dir=run_dir,
        config=AppConfig(results_dir=tmp_path),
        agent_name="omc",
        agent_version="claude 0.0-test",
        agent_command="claude",
        suite_name="runtime",
    )

    payload = json.loads(manifest_path.read_text())
    assert payload["version"] == "1.0"
    assert payload["agents"]["omc"]["command"] == "claude"
    assert payload["suites"] == ["runtime"]
    assert "environment" in payload


def test_write_suite_results_serializes_scores(tmp_path) -> None:
    store = ResultStore(tmp_path)
    run_dir = store.create_run_dir()
    report_path = store.write_suite_results(
        run_dir=run_dir,
        agent_name="omc",
        suite_name="runtime",
        scores=[
            Score(
                task_name="startup",
                agent_name="omc",
                value=75.0,
                raw={"metric": "startup_ms", "value": 123.0},
                tier=0,
                status=RunStatus.SUCCESS,
            )
        ],
    )

    payload = json.loads(report_path.read_text())
    assert payload["summary"]["task_count"] == 1
    assert payload["tasks"][0]["task_name"] == "startup"
