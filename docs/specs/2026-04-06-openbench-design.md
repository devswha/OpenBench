# OpenBench Technical Design

**Date:** 2026-04-06
**Status:** Draft
**Author:** devswha

## Document Role & Scope

This document is the **technical design / target architecture** for OpenBench.

- For **Phase 1 MVP execution scope**, use `.omx/plans/prd-openbench-mvp.md` as the authoritative product document.
- For **Phase 1 verification scope**, use `.omx/plans/test-spec-openbench-mvp.md` as the authoritative test document.
- The module layout, CLI surface, and reporting flow below describe the **target system shape across multiple phases**, not the minimum file inventory that must exist before Phase 1 implementation starts.

## Overview

OpenBench is an open-source benchmarking framework for coding agents. It provides a unified platform to compare runtime performance, task completion accuracy, and orchestration capabilities across agents like oh-my-claudecode (OMC), oh-my-codex (OMX), oh-my-openagent (OMO), and any future agent via an extensible adapter interface.

### Goals

- Comprehensive: runtime + task completion + orchestration benchmarks in one tool
- Extensible: add any agent or benchmark suite with a single file
- Community-first: public leaderboard, reproducible results, low contribution barrier
- Pragmatic: Python + Shell stack, monolithic CLI, incremental complexity

### Non-Goals

- Not a CI/CD tool (no auto-trigger on agent updates — may be added later)
- Not an agent runtime (only measures, does not host agents)
- Not a plugin marketplace (single repo, no separate packages)

## Architecture

### Directory Structure

Target architecture (future-state, not the minimum current file set):

```
OpenBench/
├── openbench/
│   ├── __init__.py
│   ├── cli.py              # CLI entrypoint (click)
│   ├── runner.py            # Benchmark execution engine
│   ├── agents/              # Agent adapters
│   │   ├── base.py          # AgentAdapter ABC
│   │   ├── omc.py           # oh-my-claudecode
│   │   ├── omx.py           # oh-my-codex
│   │   └── omo.py           # oh-my-openagent
│   ├── suites/              # Benchmark suites
│   │   ├── base.py          # BenchSuite ABC
│   │   ├── runtime/         # Tier 0: startup, memory, binary size
│   │   ├── task/            # Tier 1: SWE-bench, HumanEval, etc.
│   │   └── orchestration/   # Tier 2: multi-file edit, debugging, planning
│   ├── metrics/             # Measurement collection & normalization
│   │   ├── __init__.py
│   │   └── store.py         # ResultStore
│   ├── reporters/           # Output generation
│   │   ├── __init__.py
│   │   ├── json_reporter.py
│   │   ├── html_reporter.py
│   │   └── markdown_reporter.py
│   └── utils/               # Shared utilities
│       ├── __init__.py
│       └── process.py       # Subprocess helpers, timeout handling
├── tasks/                   # Benchmark task definitions (YAML)
│   ├── runtime/
│   ├── swe-bench-lite/
│   └── orchestration/
├── scripts/                 # Shell measurement scripts
│   ├── measure_startup.sh
│   ├── measure_memory.sh
│   └── measure_size.sh
├── results/                 # Execution results (gitignored)
├── templates/               # Jinja2 HTML templates for leaderboard
├── docs/
├── tests/
├── pyproject.toml
└── README.md
```

### Execution Flow

```
CLI (click)
  → Runner.run(agent, suite)
    → AgentAdapter.health_check()
    → AgentAdapter.setup()
    → BenchSuite.load_tasks()
    → for task in tasks:
        → AgentAdapter.run(task) → RunResult
        → BenchSuite.evaluate(run_result) → Score
        → ResultStore.save(score)
    → AgentAdapter.cleanup()
    → Reporter.generate(scores)
```

For Phase 1 MVP, the required end-to-end slice stops at **successful runtime execution + persisted results**. Report-generation workflows are planned for later phases.

## Agent Adapter Interface

All agents implement `AgentAdapter`, the single extension point for adding new agents.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class RunStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    OOM = "oom"
    CRASH = "crash"
    SETUP_ERROR = "setup_error"

@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None
    provider: str  # "anthropic", "openai", etc.

@dataclass
class Task:
    name: str
    prompt: str
    workspace: Path          # Isolated workspace for the task
    timeout: int             # Seconds
    expected: dict           # Expected outcomes for evaluation
    metadata: dict           # Suite-specific metadata

@dataclass
class RunResult:
    task: Task
    status: RunStatus
    output: str              # Agent's stdout/stderr
    duration_ms: int
    peak_memory_mb: float
    token_usage: TokenUsage | None
    files_changed: list[str]
    exit_code: int
    error_message: str | None

class AgentAdapter(ABC):
    name: str                # Unique identifier: "omc", "omx", "omo"
    display_name: str        # Human-readable: "oh-my-claudecode"
    version: str
    command: str             # Base CLI command

    @abstractmethod
    def health_check(self) -> bool:
        """Verify agent is installed and runnable."""

    @abstractmethod
    def setup(self) -> None:
        """One-time setup before benchmark run."""

    @abstractmethod
    def run(self, task: Task) -> RunResult:
        """Execute a single benchmark task."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup after benchmark run."""
```

### Auto-Discovery

Agents are discovered by scanning `openbench/agents/` for classes that subclass `AgentAdapter`. No manual registration needed.

```python
# openbench/agents/omc.py
class OMCAgent(AgentAdapter):
    name = "omc"
    display_name = "oh-my-claudecode"
    command = "claude"

    def health_check(self) -> bool:
        return shutil.which("claude") is not None

    def run(self, task: Task) -> RunResult:
        # Execute: claude -p "<prompt>" in task.workspace
        ...
```

## Benchmark Suites

### Three Tiers

| Tier | Name | What It Measures | Tools |
|------|------|------------------|-------|
| 0: Runtime | startup, memory, binary | Startup latency, RSS, disk footprint | `hyperfine`, `/usr/bin/time`, `du` |
| 1: Task Completion | SWE-bench Lite, HumanEval | Correctness rate, solve time, token cost | Shell + test harness + LLM judge |
| 2: Orchestration | multi-file edit, debug, plan | Completeness, accuracy, step count | Custom evaluators |

### Suite Interface

```python
@dataclass
class Score:
    task_name: str
    agent_name: str
    value: float             # Normalized 0-100
    raw: dict                # Raw measurement data
    tier: int

class BenchSuite(ABC):
    name: str
    tier: int                # 0, 1, or 2
    description: str

    @abstractmethod
    def load_tasks(self) -> list[Task]:
        """Load task definitions from tasks/ directory."""

    @abstractmethod
    def evaluate(self, result: RunResult) -> Score:
        """Evaluate a run result and produce a score."""
```

### Tier 0: Runtime Suite

Measured via Shell scripts wrapping standard Unix tools:

- **Startup time:** `hyperfine --warmup 3 '{command} --version'`
- **Memory usage:** `/usr/bin/time -v {command} --version` → peak RSS
- **Binary size:** `du -sh $(which {command})`

Results are numeric, no LLM judge needed.

### Tier 1: Task Completion Suite

Uses existing benchmark datasets:

- **SWE-bench Lite:** Real GitHub issues, evaluate via test suite pass/fail
- **HumanEval:** Function completion, evaluate via unit test execution

Each task is a YAML file:

```yaml
# tasks/swe-bench-lite/django-12345.yaml
name: django-12345
source: swe-bench
repo: django/django
commit: abc123
prompt: |
  Fix the issue where QuerySet.filter() raises TypeError
  when using a subquery with OuterRef.
test_command: "python -m pytest tests/queries/test_subqueries.py"
timeout: 300
```

### Tier 2: Orchestration Suite

Custom tasks that test agent orchestration capabilities:

- **Multi-file edit:** "Add input validation to all API endpoints"
- **Debug:** "Fix the failing test in test_auth.py" (given a repo with a known bug)
- **Planning:** "Refactor the monolith into 3 microservices" (evaluate plan quality)

Evaluation uses a combination of:
- Deterministic checks (files changed, tests pass)
- LLM judge for subjective quality (plan coherence, code quality)

```yaml
# tasks/orchestration/multi-file-edit.yaml
name: multi-file-edit
description: "Add error handling to 3 API endpoint files"
prompt: "Add input validation and error handling to all API endpoints in src/api/"
workspace_repo: "https://github.com/openbench/test-repos/api-server"
expected:
  files_changed_min: 3
  tests_pass: true
  no_regressions: true
evaluation:
  - type: deterministic
    check: files_changed_min
  - type: deterministic
    check: tests_pass
  - type: llm_judge
    criteria: "code quality, error messages, edge case coverage"
timeout: 300
```

### Task Validation

All task YAML files should be validated against a typed schema on load. This catches missing fields, wrong types, and suite-specific misconfigurations before any agent runs. Phase 1 may use **pydantic or an equivalent validation approach**, but the chosen implementation must match `pyproject.toml` dependencies.

Example if pydantic is chosen:

```python
from pydantic import BaseModel

class TaskDefinition(BaseModel):
    name: str
    prompt: str
    timeout: int = 300
    # SWE-bench specific
    source: str | None = None
    repo: str | None = None
    commit: str | None = None
    test_command: str | None = None
    # Orchestration specific
    workspace_repo: str | None = None
    expected: dict | None = None
    evaluation: list[dict] | None = None
```

## Results Storage & Metrics

`ResultStore` persists scores to disk after each task evaluation, writing JSON files under `results/`. It is the single writer of benchmark output and serves as the source of truth for all reporters.

### Core Metrics

| Metric | Tier 0 | Tier 1 | Tier 2 |
|--------|--------|--------|--------|
| Duration (ms) | Y | Y | Y |
| Peak Memory (MB) | Y | Y | Y |
| Binary Size (MB) | Y | - | - |
| Correctness (0-100) | - | Y | Y |
| Token Usage | - | Y | Y |
| Files Changed | - | Y | Y |
| LLM Judge Score | - | - | Y |

### Normalization

All scores are normalized to 0-100 for cross-suite comparison:
- Correctness: percentage of tests passed
- LLM judge: 0-100 rating from the judge model
- Runtime metrics: log-scaled so that the reference value earns 50 points (lower is better → higher score)

```python
import math

def normalize_runtime(value_ms: float, reference_ms: float = 1000.0) -> float:
    """Score 0-100 where reference_ms gets 50 points.
    Uses log scale to handle wide variance (50ms vs 10000ms)."""
    if value_ms <= 0:
        return 100.0
    ratio = reference_ms / value_ms
    score = 50.0 + 50.0 * math.log2(ratio) / math.log2(10)
    return max(0.0, min(100.0, score))
```

Reference values are configurable per suite via `openbench.toml` or CLI flags. Default references: startup 1000ms, memory 512MB, binary size 100MB.

### Directory Layout

```
results/
├── 2026-04-06T12-00-00/
│   ├── manifest.json          # Run metadata
│   ├── omc/
│   │   ├── runtime.json       # Tier 0 results
│   │   ├── task.json          # Tier 1 results
│   │   └── orchestration.json # Tier 2 results
│   └── omx/
│       └── ...
└── latest/                    # Symlink to most recent run
```

### Manifest Schema

The example below shows the long-horizon manifest shape. Phase 1 may persist only the `runtime` suite for `omc`, but it should preserve the same core metadata fields and versioning strategy.

```json
{
  "version": "1.0",
  "timestamp": "2026-04-06T12:00:00Z",
  "agents": {
    "omc": { "version": "3.4.1", "command": "claude" },
    "omx": { "version": "1.2.0", "command": "codex" },
    "omo": { "version": "0.8.0", "command": "openagent" }
  },
  "suites": ["runtime", "swe-bench-lite", "orchestration"],
  "judge_model": "claude-sonnet-4-20250514",
  "normalization_references": {
    "startup_ms": 1000,
    "memory_mb": 512,
    "binary_size_mb": 100
  },
  "environment": {
    "os": "Linux 6.8.0",
    "cpu": "AMD Ryzen 9 7950X",
    "memory_gb": 64,
    "python": "3.11.9"
  }
}
```

## CLI Interface

### Phase 1 MVP CLI (authoritative for initial implementation)

```bash
# Run the MVP runtime slice
openbench run --agent omc --suite runtime

# List available agents and suites
openbench list agents
openbench list suites

# Check environment readiness
openbench doctor
```

### Planned post-MVP CLI surface

```bash
# Run all suites for all agents
openbench run

# Run specific agent + suite
openbench run --agent omc --suite runtime
openbench run --agent omc,omx --suite runtime,swe-bench-lite

# List available agents and suites
openbench list agents
openbench list suites

# Generate reports
openbench report                    # JSON to stdout
openbench report --format html      # Interactive HTML leaderboard
openbench report --format markdown  # Markdown table

# Check agent availability
openbench doctor
```

### CLI Commands

| Command | Availability | Description |
|---------|--------------|-------------|
| `run` | Phase 1 MVP | Execute benchmarks |
| `list` | Phase 1 MVP | List available agents/suites |
| `doctor` | Phase 1 MVP | Check agent installations |
| `report` | Post-MVP | Generate reports from results |
| `compare` | Post-MVP | Compare two result sets |

## Leaderboard

HTML leaderboard generated via Jinja2 + Plotly:

- **Overall ranking:** Weighted composite score across all tiers
- **Per-tier breakdown:** Sortable tables with individual metrics
- **Charts:** Bar charts for runtime, radar charts for capabilities
- **History:** Score trends over time (if multiple runs exist)

Default tier weights: Runtime 20%, Task Completion 40%, Orchestration 40%.
Weights are configurable via CLI flag or config file.

## Testing Strategy

| Layer | What to Test | How |
|-------|-------------|-----|
| Agent adapters | health_check, run contract | Mock subprocess, verify command construction |
| Suites | Task loading, score evaluation | Unit tests with fixture YAML |
| Runner | Orchestration flow | Integration test with mock agent + mock suite |
| CLI | Command parsing, output format | Click test runner |
| Reporters | Output correctness | Snapshot tests |

## Implementation Priority

### Phase 1: Foundation (MVP)
1. `AgentAdapter` base class + OMC adapter
2. Runtime suite (Tier 0) — startup, memory, binary size
3. `Runner` execution engine
4. `ResultStore` + manifest persistence
5. CLI (`run`, `list`, `doctor`)
6. Task dataclass finalization (`RunStatus`, `TokenUsage`)
7. Temp-directory `WorkspaceManager` protocol definition
8. Task YAML validation + minimal `openbench.toml` parsing

### Phase 2: Task Completion
9. `BenchSuite` base class hardening
10. OMX + OMO adapters
11. SWE-bench Lite integration + deterministic evaluator
12. Task-completion task loader expansion

### Phase 3: Orchestration & Reporting
13. Orchestration suite with custom tasks
14. LLM judge evaluator
15. HTML leaderboard with Plotly charts
16. Markdown reporter + `report` / `compare` workflows
17. Task-level parallel execution (asyncio/concurrent.futures)

### Phase 4: Polish
18. CI/CD integration (GitHub Actions)
19. Contribution guide
20. Test repo fixtures
21. Documentation site

## Phase 1 Decisions Fixed

- **Execution scope:** Phase 1 implements one adapter (`omc`), one suite (`runtime`), one persisted result path, and the `run` / `list` / `doctor` CLI path.
- **Workspace isolation:** Phase 1 uses temp directories. Docker and git-worktree isolation are deferred.
- **Judge policy:** Phase 1 uses no LLM judge. Runtime benchmarking remains deterministic.
- **Result versioning:** Phase 1 writes schema version `1.0` metadata in `manifest.json` under `results/<timestamp>/`.
- **Config scope:** Phase 1 may support a minimal `openbench.toml` limited to results directory and normalization references. CLI flags override config defaults.

## Later-Phase Open Decisions

- **LLM judge model:** Which model to use for Tier 2 evaluation once orchestration scoring lands? (Claude, GPT-4, or configurable)
  **Recommendation:** Configurable with default Claude Sonnet. Add an `LLMJudge` protocol so the judge backend is swappable. Record the judge model used in `manifest.json` for reproducibility.

- **Test repos:** Host fixture repos under an OpenBench GitHub org, or inline in the repo?
  **Recommendation:** Separate GitHub org (`github.com/openbench`), referenced by URL in task YAML. Local cache at `~/.openbench/repos/` to avoid repeated clones.

- **Token counting:** Each agent tracks tokens differently — standardize or report as-is?
  **Recommendation:** Report as-is per agent via the `TokenUsage` dataclass. Add estimated cost (USD) as a secondary metric via `estimated_cost_usd` field. No forced standardization — transparency over false precision.
