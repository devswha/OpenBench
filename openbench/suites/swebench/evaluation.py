"""Test result parsing for SWE-bench evaluation."""
from __future__ import annotations

import json


def parse_fail_to_pass(instance: dict) -> list[str]:
    """Extract the list of tests that must change from fail to pass."""
    raw = instance.get("FAIL_TO_PASS", "[]")
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, list):
        return raw
    return []


def check_tests_passed(test_output: str, fail_to_pass: list[str]) -> bool:
    """Check whether all fail-to-pass tests are now passing.

    Simple heuristic: if all test identifiers appear in output without
    FAILED/ERROR markers, consider them passed.
    """
    if not fail_to_pass:
        return False

    # Check for explicit failures
    for test_id in fail_to_pass:
        # Extract short test name (last component)
        short_name = test_id.rsplit("::", 1)[-1] if "::" in test_id else test_id.rsplit(".", 1)[-1]
        # If the test appears with FAIL or ERROR, it didn't pass
        for line in test_output.splitlines():
            if short_name in line and ("FAIL" in line or "ERROR" in line):
                return False

    # If no explicit failures found and test output is non-empty, consider passed
    # Also check for common success indicators
    if "passed" in test_output.lower() or "ok" in test_output.lower():
        return True

    # If test output contains no failure markers at all
    return "FAIL" not in test_output and "ERROR" not in test_output


def determine_test_command(instance: dict) -> str:
    """Derive the test command for a given instance.

    Uses the FAIL_TO_PASS test identifiers to build the command.
    """
    repo = instance.get("repo", "")
    fail_to_pass = parse_fail_to_pass(instance)

    if not fail_to_pass:
        return "python -m pytest -xvs"

    # Django uses its own test runner
    if "django" in repo:
        # Django test IDs are like "tests.module.TestClass.test_method"
        test_labels = set()
        for test_id in fail_to_pass:
            # Take the module path (drop the test method)
            parts = test_id.rsplit(".", 1)
            test_labels.add(parts[0] if len(parts) > 1 else test_id)
        labels = " ".join(sorted(test_labels))
        return f"python -m django test {labels} --settings=django.conf.global_settings --parallel 1"

    # Most other repos use pytest
    test_files = set()
    for test_id in fail_to_pass:
        # pytest IDs: path/to/test.py::TestClass::test_method
        if "::" in test_id:
            test_files.add(test_id.split("::")[0])
        else:
            # Module-style: tests.module.TestClass.test_method
            test_files.add(test_id)

    files = " ".join(sorted(test_files))
    return f"python -m pytest -xvs {files}"
