# OpenBench

Open benchmarking framework for coding agents.

Compare runtime performance, task completion, and orchestration capabilities across coding agents like oh-my-claudecode, oh-my-codex, oh-my-openagent, and more.

## Features

- **Runtime benchmarks** — Startup time, memory usage, binary size
- **Task completion benchmarks** — SWE-bench, HumanEval, and custom task sets
- **Orchestration benchmarks** — Multi-file editing, debugging, planning capabilities
- **Extensible** — Add any agent or benchmark suite with a single file
- **Leaderboard** — Auto-generated HTML reports with interactive charts

## Quick Start

```bash
pip install -e ".[dev]"
openbench run --agent omc --suite runtime
openbench report --format html
```

## Adding an Agent

Create a file in `openbench/agents/`:

```python
from openbench.agents.base import AgentAdapter

class MyAgent(AgentAdapter):
    name = "my-agent"

    def setup(self) -> None:
        ...

    def run(self, task: Task) -> RunResult:
        ...
```

## Adding a Benchmark Suite

Create a directory in `tasks/` with a `suite.yaml` definition and task files.

## License

MIT
