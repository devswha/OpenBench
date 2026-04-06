from __future__ import annotations

import json

import pytest
from openbench.config import load_config
from openbench.runner import Runner


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_run_runtime_persists_results(agent_name: str, shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run(agent_name, "runtime")

    assert summary.manifest_path.exists()
    assert summary.suite_report_path.exists()
    assert summary.run_dir.exists()


@pytest.mark.parametrize("agent_name", ["omc", "omx"])
def test_runtime_results_include_expected_metrics(agent_name: str, shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run(agent_name, "runtime")
    payload = json.loads(summary.suite_report_path.read_text())
    metrics = {task["raw"]["metric"]: task for task in payload["tasks"]}

    assert set(metrics) == {"startup_ms", "memory_mb", "binary_size_mb"}
    assert metrics["startup_ms"]["raw"]["available"] is True
    assert metrics["memory_mb"]["raw"]["available"] is True
    assert metrics["binary_size_mb"]["raw"]["available"] is True


def test_omc_shim_runs_without_network(shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run("omc", "runtime")

    assert summary.had_failures is False


def test_omx_shim_runs_without_network(shim_env, tmp_path) -> None:
    config = load_config(results_dir_override=tmp_path / "results")

    summary = Runner(config).run("omx", "runtime")

    assert summary.had_failures is False
