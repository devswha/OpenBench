# OpenBench Design Spec

**Date:** 2026-04-06
**Status:** Draft
**Author:** devswha

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
│   │   └── collector.py     # MetricsCollector
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
        → AgentAdapter.run(task)
        → MetricsCollector.collect(run_result)
        → BenchSuite.evaluate(run_result) → Score
    → AgentAdapter.cleanup()
    → Reporter.generate(scores)
```

## Agent Adapter Interface

All agents implement `AgentAdapter`, the single extension point for adding new agents.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

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
    success: bool
    output: str              # Agent's stdout/stderr
    duration_ms: int
    peak_memory_mb: float
    token_usage: int | None  # API token count if available
    files_changed: list[str]
    exit_code: int

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

## Metrics Collection

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
- Runtime metrics: inverse-scaled (lower is better → higher score)
- Correctness: percentage of tests passed
- LLM judge: 0-100 rating from the judge model

## Results Storage

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

```json
{
  "version": "1.0",
  "timestamp": "2026-04-06T12:00:00Z",
  "agents": ["omc", "omx", "omo"],
  "suites": ["runtime", "swe-bench-lite", "orchestration"],
  "environment": {
    "os": "Linux 6.8.0",
    "cpu": "AMD Ryzen 9 7950X",
    "memory_gb": 64,
    "python": "3.11.9"
  }
}
```

## CLI Interface

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

| Command | Description |
|---------|-------------|
| `run` | Execute benchmarks |
| `list` | List available agents/suites |
| `report` | Generate reports from results |
| `doctor` | Check agent installations |
| `compare` | Compare two result sets |

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
4. JSON reporter
5. CLI (`run`, `list`, `doctor`)

### Phase 2: Task Completion
6. `BenchSuite` base class + SWE-bench Lite integration
7. Task YAML loader
8. Deterministic evaluator
9. OMX + OMO adapters

### Phase 3: Orchestration & Reporting
10. Orchestration suite with custom tasks
11. LLM judge evaluator
12. HTML leaderboard with Plotly charts
13. Markdown reporter
14. `compare` command

### Phase 4: Polish
15. CI/CD integration (GitHub Actions)
16. Contribution guide
17. Test repo fixtures
18. Documentation site

## Open Decisions

- **LLM judge model:** Which model to use for Tier 2 evaluation? (Claude, GPT-4, or configurable)
- **Test repos:** Host fixture repos under an OpenBench GitHub org, or inline in the repo?
- **Token counting:** Each agent tracks tokens differently — standardize or report as-is?
- **Workspace isolation:** Docker containers vs temp directories vs git worktrees?
