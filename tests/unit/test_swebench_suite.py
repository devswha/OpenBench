from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from openbench.config import AppConfig
from openbench.suites.swebench.suite import SweBenchSuite


def test_swebench_suite_load_tasks(tmp_path):
    """Test that SweBenchSuite.load_tasks reads suite.yaml + instances.json correctly."""
    instances = [
        {
            "instance_id": "test__repo-123",
            "repo": "test/repo",
            "base_commit": "abc123",
            "problem_statement": "Fix the bug described here.",
            "patch": "diff --git ...",
            "test_patch": "diff --git ...",
            "version": "1.0",
            "FAIL_TO_PASS": '["tests/test_foo.py::test_bar"]',
            "PASS_TO_PASS": "[]",
        }
    ]

    suite_yaml = {
        "name": "swe-bench",
        "tier": 2,
        "description": "test",
        "defaults": {"timeout": 300},
        "instances": [
            {"id": "test__repo-123", "difficulty": "easy", "category": "bugfix"}
        ],
    }

    swebench_dir = tmp_path / "tasks" / "swe-bench"
    swebench_dir.mkdir(parents=True)
    (swebench_dir / "instances.json").write_text(json.dumps(instances))
    (swebench_dir / "suite.yaml").write_text(yaml.dump(suite_yaml))

    config = AppConfig()
    suite = SweBenchSuite(config)

    suite.definition_path = lambda: swebench_dir / "suite.yaml"
    suite.instances_path = lambda: swebench_dir / "instances.json"

    tasks = suite.load_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "test__repo-123"
    assert "Fix the bug" in tasks[0].prompt
    assert tasks[0].metadata["difficulty"] == "easy"
    assert tasks[0].metadata["category"] == "bugfix"
    assert tasks[0].timeout == 300


def test_swebench_suite_load_tasks_missing_instances(tmp_path):
    """Test that load_tasks raises when instances.json is missing."""
    suite_yaml = {
        "name": "swe-bench",
        "instances": [{"id": "foo__bar-1", "difficulty": "easy", "category": "bugfix"}],
    }

    swebench_dir = tmp_path / "tasks" / "swe-bench"
    swebench_dir.mkdir(parents=True)
    (swebench_dir / "suite.yaml").write_text(yaml.dump(suite_yaml))

    config = AppConfig()
    suite = SweBenchSuite(config)
    suite.definition_path = lambda: swebench_dir / "suite.yaml"
    suite.instances_path = lambda: swebench_dir / "instances.json"

    with pytest.raises(ValueError, match="instances not found"):
        suite.load_tasks()
