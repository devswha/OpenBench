from __future__ import annotations

from openbench.suites.swebench.evaluation import (
    parse_fail_to_pass,
    check_tests_passed,
    determine_test_command,
)


def test_parse_fail_to_pass_from_json_string():
    instance = {"FAIL_TO_PASS": '["tests.test_foo.TestBar.test_baz"]'}
    result = parse_fail_to_pass(instance)
    assert result == ["tests.test_foo.TestBar.test_baz"]


def test_parse_fail_to_pass_from_list():
    instance = {"FAIL_TO_PASS": ["test_a", "test_b"]}
    result = parse_fail_to_pass(instance)
    assert result == ["test_a", "test_b"]


def test_parse_fail_to_pass_missing():
    result = parse_fail_to_pass({})
    assert result == []


def test_check_tests_passed_with_success():
    output = "test_baz PASSED\n1 passed, 0 failed"
    assert check_tests_passed(output, ["tests.test_foo::test_baz"]) is True


def test_check_tests_passed_with_failure():
    output = "test_baz FAILED\n0 passed, 1 failed"
    assert check_tests_passed(output, ["tests.test_foo::test_baz"]) is False


def test_check_tests_passed_empty_tests():
    assert check_tests_passed("anything", []) is False


def test_determine_test_command_django():
    instance = {
        "repo": "django/django",
        "FAIL_TO_PASS": '["tests.auth_tests.test_views.LoginViewTest.test_login"]',
    }
    cmd = determine_test_command(instance)
    assert "runtests.py" in cmd
    assert "auth_tests" in cmd


def test_determine_test_command_pytest():
    instance = {
        "repo": "psf/requests",
        "FAIL_TO_PASS": '["tests/test_requests.py::TestRequests::test_get"]',
    }
    cmd = determine_test_command(instance)
    assert "pytest" in cmd
    assert "tests/test_requests.py" in cmd
