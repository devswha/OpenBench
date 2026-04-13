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

    Returns False if: no tests to check, Docker/infrastructure error detected,
    or any fail_to_pass test has FAIL/ERROR markers in output.
    Returns True only if test output contains positive signals (passed/ok)
    and no failure markers for the expected tests.
    """
    if not fail_to_pass:
        return False

    # Infrastructure errors — not a valid test run
    infra_errors = ["pull access denied", "repository does not exist", "docker:", "No such file or directory"]
    for marker in infra_errors:
        if marker in test_output:
            return False

    # Must have actual test output (not just Docker errors or empty)
    stripped = test_output.strip()
    if not stripped:
        return False

    # Check for explicit failures in fail_to_pass tests
    for test_id in fail_to_pass:
        short_name = test_id.rsplit("::", 1)[-1] if "::" in test_id else test_id.rsplit(".", 1)[-1]
        for line in test_output.splitlines():
            if short_name in line and ("FAIL" in line or "ERROR" in line):
                return False

    # Must have a positive test-passed signal
    lower = test_output.lower()
    if "passed" in lower or "\nok\n" in lower or "\nok" == lower[-3:]:
        return True

    return False


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
