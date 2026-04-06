# OpenBench MVP Test Specification

- **Status:** Draft
- **Date:** 2026-04-06
- **Owner:** devswha
- **Authority:** Phase 1 MVP verification scope lives in this test spec; the design doc remains a broader architecture reference.
- **Related PRD:** `.omx/plans/prd-openbench-mvp.md`
- **Source design:** `docs/specs/2026-04-06-openbench-design.md`

## 1. Test Objective

Verify that the OpenBench MVP vertical slice is real, reproducible, and aligned with the documented CLI surface. The MVP passes only if one adapter (`omc`), one suite (`runtime`), one result path, and one CLI path (`run`, `list`, `doctor`) work together and can be validated without relying on a live external agent account.

## 2. Test Scope

### In scope
- CLI behavior for `run`, `list`, `doctor`
- adapter contract and OMC adapter health/run integration points
- runtime suite measurement/parsing behavior
- result persistence and manifest schema
- README/entrypoint/dependency alignment checks
- deterministic shim-based smoke coverage

### Out of scope
- Tier 1 and Tier 2 evaluation correctness
- HTML/Markdown/report generation workflows
- multi-agent comparisons
- Docker isolation behavior
- real network-backed LLM judging

## 3. Test Environment Assumptions

- Python runtime for implementation/tests is **3.11+**
- `pytest` is the test runner
- CLI tests may use Click's `CliRunner`
- automated tests use a fixture shim executable on `PATH` instead of a real `claude` installation
- runtime measurement commands may be stubbed or wrapped in fixtures where host tools are unavailable

## 4. Verification Layers

### 4.1 Unit tests

Unit tests should cover isolated behavior with no external process dependency beyond controlled fixtures.

Suggested targets:
- task/result models and enum behavior
- adapter base-class contract
- OMC adapter command construction and health-check behavior
- runtime suite task loading and metric parsing
- normalization helpers
- manifest/result serialization logic
- config parsing for minimal `openbench.toml`

### 4.2 Integration tests

Integration tests should exercise the real runner across collaborating components.

Suggested targets:
- runner + OMC shim adapter + runtime suite + result store
- result-directory creation and manifest writing
- propagation of tool-unavailable / setup-error conditions
- CLI `run` orchestration from command input to persisted output

### 4.3 CLI tests

CLI tests should validate:
- command registration
- option parsing
- user-facing output
- exit codes for success and known failures
- help text for `run`, `list`, and `doctor`

### 4.4 Smoke tests

Smoke tests should prove the advertised user journey works in a near-real invocation path.

Required smoke path:
1. install in editable mode or invoke the module entrypoint
2. verify `list agents`
3. verify `list suites`
4. verify `doctor`
5. verify `run --agent omc --suite runtime` with a local shim executable and isolated results dir

## 5. Acceptance-Criteria Mapping

| Acceptance Criterion | Required automated proof |
| --- | --- |
| AC-1 `list agents` returns `omc` | CLI test: `test_list_agents_shows_omc` |
| AC-2 `list suites` returns `runtime` | CLI test: `test_list_suites_shows_runtime` |
| AC-3 `doctor` reports command/tool availability correctly | CLI test: `test_doctor_reports_ready_state`; integration test: `test_doctor_reports_missing_tool` |
| AC-4 `run --agent omc --suite runtime` writes `manifest.json` and `omc/runtime.json` | integration test: `test_run_runtime_persists_results` |
| AC-5 runtime results include startup/memory/binary-size metrics or explicit unavailable states | integration test: `test_runtime_results_include_expected_metrics` |
| AC-6 manifest includes schema/env/agent/suite metadata | unit/integration test: `test_manifest_contains_required_metadata` |
| AC-7 README quick start is aligned and smoke-testable | doc alignment test/check: `test_readme_quickstart_matches_cli_surface` + smoke script |
| AC-8 MVP is testable without network/live account | integration test: `test_omc_shim_runs_without_network` |

## 6. Proposed Test Inventory

### Unit
- `tests/unit/test_models.py`
- `tests/unit/test_agent_base.py`
- `tests/unit/test_omc_adapter.py`
- `tests/unit/test_runtime_suite.py`
- `tests/unit/test_normalization.py`
- `tests/unit/test_result_store.py`
- `tests/unit/test_config.py`

### Integration
- `tests/integration/test_runner_runtime_flow.py`
- `tests/integration/test_result_persistence.py`
- `tests/integration/test_cli_run_runtime.py`

### CLI
- `tests/cli/test_list_command.py`
- `tests/cli/test_doctor_command.py`
- `tests/cli/test_run_command.py`

### Smoke / scripts
- `tests/smoke/test_runtime_smoke.py` or equivalent scripted smoke harness
- fixture executable under `tests/fixtures/bin/claude`

## 7. Required Fixtures and Test Utilities

- **Shim OMC executable**: a small script on `PATH` that behaves like the expected `claude --version` and runtime command surface needed by the adapter
- **Temporary results directory fixture**: isolates run artifacts per test
- **Runtime-tool fixture/stub**: allows deterministic startup/memory/size outputs even when host tooling differs
- **Sample task definitions**: minimal runtime YAML fixtures under `tasks/runtime/` or `tests/fixtures/tasks/`

## 8. Exit Criteria For Phase 1

Phase 1 verification is complete only when all are true:

1. `python -m pytest -q` passes on supported Python (3.11+)
2. all named acceptance-criteria tests pass
3. smoke path succeeds with shim executable
4. `pyproject.toml` entrypoint matches the implemented CLI module
5. README quick-start commands match supported CLI behavior
6. dependency declarations match implementation reality (for example, if pydantic is used, it is declared)

## 9. Verification Commands

Use these commands as the default verification path after implementation:

```bash
python -m pytest -q
python -m pytest tests/cli -q
python -m pytest tests/integration -q
python -m pytest tests/unit -q
python -m openbench.cli list agents
python -m openbench.cli list suites
python -m openbench.cli doctor
python -m openbench.cli run --agent omc --suite runtime --results-dir /tmp/openbench-results
```

If the editable install path is available, the equivalent smoke commands may also be run as:

```bash
openbench list agents
openbench list suites
openbench doctor
openbench run --agent omc --suite runtime --results-dir /tmp/openbench-results
```

## 10. Known Risks / Watchpoints

- Python 3.10 environments will fail the declared version requirement; tests must run on 3.11+
- host runtime tools may vary; tests must avoid assuming tool presence unless explicitly part of the fixture setup
- README drift can reintroduce false quick-start claims; keep doc alignment as a test/check, not a manual convention
- using real agent CLIs in automated tests will make CI flaky; keep shim-based coverage mandatory

## 11. Execution Approval Gate

Implementation handoff should be considered approved only when:

1. this test-spec exists and is accepted alongside the PRD
2. each PRD acceptance criterion maps to at least one named test/check
3. the initial implementation plan includes the required fixtures/utilities
4. the vertical-slice scope remains limited to one adapter, one suite, one result path, and one CLI path set
