# OpenBench MVP PRD

- **Status:** Draft
- **Date:** 2026-04-06
- **Owner:** devswha
- **Authority:** Phase 1 MVP product scope lives in this PRD; the design doc is architectural reference only.
- **Source design:** `docs/specs/2026-04-06-openbench-design.md`
- **Related context:** `.omx/context/review-current-spec-docs-20260406T071134Z.md`

## 1. Problem Statement

OpenBench needs a credible MVP that can benchmark coding-agent CLIs without overreaching into every planned benchmark tier at once. The current design document defines a strong architecture direction, but the repository does not yet have an execution-ready scope, acceptance criteria, or test mapping. This PRD narrows the first deliverable to a strict vertical slice that proves the framework can discover an agent, run a deterministic runtime suite, and persist reproducible results.

## 2. Desired Outcome

Deliver a Phase 1 OpenBench MVP that can:

1. expose a working CLI with `run`, `list`, and `doctor`
2. benchmark one real agent adapter (`omc`)
3. run one benchmark suite (`runtime`)
4. persist one complete result set to disk with manifest metadata
5. support deterministic verification in automated tests without requiring a live external agent account

## 3. Users and Jobs-to-be-Done

### Primary users
- **OpenBench maintainer** — wants a trustworthy baseline implementation to build on
- **Contributor adding adapters/suites** — wants a clear extension seam and a passing test harness
- **Evaluator comparing agent runtimes** — wants repeatable runtime measurements and inspectable results

### Jobs-to-be-done
- “Run a benchmark and get a persisted result set I can inspect later.”
- “See which agents and suites are currently available.”
- “Check whether my environment is ready before I run benchmarks.”

## 4. Product Goals

- Prove the end-to-end OpenBench loop with one adapter and one suite
- Establish repo/doc/code alignment for the advertised MVP commands
- Prioritize reproducibility and verification over breadth
- Preserve the extension model described in the design doc

## 5. Non-Goals for MVP

The following are explicitly out of scope for Phase 1:

- OMX and OMO adapters
- Tier 1 task-completion suites
- Tier 2 orchestration suites
- LLM-judge integration
- HTML leaderboard, Markdown reporting, and `compare`
- CI/CD automation beyond basic local/CI test execution
- Docker-based isolation
- Public leaderboard hosting or docs site work

## 6. MVP Scope

### 6.1 Phase 1 strict vertical slice

Phase 1 is complete only when all of the following are true:

1. **One working agent adapter**: `omc`
2. **One working suite**: `runtime`
3. **One persisted result path**: timestamped result directory with manifest + suite output
4. **One working CLI path**: `run`, `list`, `doctor`

### 6.2 In-scope deliverables

- `openbench/cli.py` implementing `run`, `list`, `doctor`
- `openbench/runner.py` for end-to-end orchestration
- `openbench/agents/base.py` and `openbench/agents/omc.py`
- `openbench/suites/base.py` and runtime-suite implementation
- `openbench/metrics/store.py` for manifest/result persistence
- minimal utility layer for subprocess handling and filesystem paths
- runtime measurement task definitions under `tasks/runtime/`
- tests covering unit, integration, CLI, and smoke requirements
- README updates only after commands are real and testable

### 6.3 Out-of-scope follow-ons

- `report` command as a separate user workflow
- reporter modules beyond the minimum persistence needed for `run`
- auto-discovery beyond the initial adapter/suite registration approach needed to ship Phase 1
- user-configurable weighting across all benchmark tiers

## 7. Functional Requirements

### FR-1: CLI commands
OpenBench MUST expose:
- `openbench run`
- `openbench list`
- `openbench doctor`

### FR-2: Listing
`openbench list agents` MUST show at least `omc`.
`openbench list suites` MUST show at least `runtime`.

### FR-3: Doctor checks
`openbench doctor` MUST report whether the OMC adapter command is available and whether required runtime tools for the runtime suite are available. It MUST fail clearly when the environment is not ready.

### FR-4: Runtime benchmark execution
`openbench run --agent omc --suite runtime` MUST execute the runtime suite through the runner and produce structured results.

### FR-5: Result persistence
Each run MUST write a timestamped result directory containing:
- `manifest.json`
- one suite result file for the executed agent, at minimum `omc/runtime.json`

### FR-6: Reproducibility metadata
The manifest MUST capture enough metadata to explain a result:
- OpenBench schema version
- timestamp
- agent identity and command
- selected suites
- normalization references
- environment info (OS, Python, CPU when available)

### FR-7: Deterministic testability
The MVP MUST be testable in CI with a shim/fake executable on `PATH`; automated verification MUST NOT require a live Claude account or network round-trip.

### FR-8: Documentation alignment
README quick-start examples MUST match the actually implemented commands. `pyproject.toml` entrypoints and dependency declarations MUST match the implementation.

## 8. Proposed Decisions To Close Before Execution

### D-1: Workspace isolation
**Decision:** Use temporary directories in Phase 1.

**Why:** zero extra dependencies, easy cleanup, sufficient for runtime-only measurements.

**Deferred:** Docker and git-worktree isolation.

### D-2: Judge / reproducibility policy
**Decision:** Phase 1 uses no LLM judge. Runtime suite remains deterministic.

**Why:** runtime benchmarking does not need subjective evaluation; this avoids premature judge-policy complexity.

### D-3: `openbench.toml` ownership and schema
**Decision:** Phase 1 supports an optional minimal config file with only:
- `results_dir`
- runtime normalization references (`startup_ms`, `memory_mb`, `binary_size_mb`)
- default tier weights placeholder only if needed by persistence code

CLI flags override config-file defaults.

### D-4: Result versioning
**Decision:** Persist schema version `1.0` in `manifest.json` and write results under `results/<timestamp>/`.

A `latest` symlink may be added later, but it is not a Phase 1 blocker.

## 9. Acceptance Criteria

- **AC-1**: `openbench list agents` returns `omc`
- **AC-2**: `openbench list suites` returns `runtime`
- **AC-3**: `openbench doctor` reports command/tool availability with correct exit behavior
- **AC-4**: `openbench run --agent omc --suite runtime` produces a result directory with `manifest.json` and `omc/runtime.json`
- **AC-5**: persisted runtime results contain startup, memory, and binary-size measurements or explicit unavailable/error states
- **AC-6**: manifest includes schema version, environment metadata, agent metadata, and selected suite information
- **AC-7**: README quick-start commands are smoke-testable against the shipped implementation
- **AC-8**: automated tests can validate MVP behavior with a local shim executable and without network dependency

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| External CLI tools differ across machines | inconsistent results | doctor output must show missing tools clearly; manifest records environment/tool context |
| Runtime metrics are flaky | low confidence in comparisons | normalize only after raw capture; store raw values and error states |
| OMC CLI unavailable in CI | tests become non-deterministic | use shim executable in automated tests |
| README drifts from implementation | user trust erosion | make README alignment part of acceptance criteria |
| Config/file-layout decisions expand too early | MVP slips | keep schema minimal and defer broad config/reporting work |

## 11. Execution Handoff Gate

No execution mode (`ralph`, `team`) should begin implementation until all of the following planning artifacts and checks are in place:

1. `docs/specs/2026-04-06-openbench-design.md` is treated as technical design only
2. `.omx/plans/prd-openbench-mvp.md` exists
3. `.omx/plans/test-spec-openbench-mvp.md` exists
4. the PRD and test-spec agree on the same MVP scope and acceptance criteria
5. the implementation plan targets `run`, `list`, and `doctor` first

## 12. Follow-up After MVP

After Phase 1 is complete and verified, the next planning increment should choose one of:
- add OMX + OMO adapters
- add Tier 1 task-completion benchmarking
- add report-generation workflows
- add more robust isolation options
