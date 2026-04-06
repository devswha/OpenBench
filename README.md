# OpenBench

Open benchmarking framework for coding agents.

Compare runtime performance, task completion, and orchestration capabilities across coding agents like oh-my-claudecode, oh-my-codex, oh-my-openagent, and more.

## Phase 1 MVP Scope

The current MVP implements a strict vertical slice:
- **Runtime adapters available now** — `omc`, `omx`
- **One suite** — `runtime`
- **One persisted result path** — timestamped run directories under `results/`
- **One CLI path set** — `run`, `list`, `doctor`

Post-MVP features such as report generation, multi-agent comparisons, and orchestration/task-completion suites are planned but not yet implemented.

## Quick Start

```bash
pip install -e ".[dev]"
openbench doctor
openbench list agents
openbench list suites
openbench run --agent omc --suite runtime
openbench run --agent omx --suite runtime
```

## What `doctor` checks

The MVP `doctor` command verifies:
- the configured OMC command is available
- `hyperfine` is available for startup measurement
- GNU `time` is available for memory measurement
- `du` is available for binary-size measurement

## Adding an Agent

Create a file in `openbench/agents/` that follows the `AgentAdapter` contract used by the MVP adapter implementation.

## Adding a Benchmark Suite

Create task definitions under `tasks/` and implement a suite class under `openbench/suites/`.

## License

MIT
