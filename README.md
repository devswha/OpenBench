# OpenBench

**Open benchmarking framework for coding-agent CLIs.**

OpenBench measures coding agents on identical tasks, identical environments, and reports results you can compare side-by-side.

**Live results:** [devswha.github.io/OpenBench](https://devswha.github.io/OpenBench/)

---

## What it measures

| Suite | Tasks | What it tests |
|-------|-------|---------------|
| **Practical** (Tier 0) | 5 self-contained fixtures | Bug fixes, feature additions, refactoring — fast CI validation |
| **SWE-bench** (Tier 1) | 50 real GitHub issues | Production-grade coding on Django, Sympy, scikit-learn, matplotlib, Flask, Requests |
| **Runtime** | 3 CLI metrics | Startup latency, peak memory, binary size |

## Agents

| Agent | CLI | Description |
|-------|-----|-------------|
| `claude` | `claude` | Claude Code (native, no plugins) |
| `omc` | `claude` | oh-my-claudecode (Claude Code + OMC plugins/hooks) |
| `codex` | `codex` | OpenAI Codex CLI (native) |
| `omx` | `omx` | oh-my-codex (Codex CLI + OMX wrapper) |

## Latest Results (2026-04-13)

### Practical (5 Easy tasks, all agents 5/5 pass)

| Agent | Time | Tokens (in) |
|-------|------|-------------|
| claude | **93s** | 834k |
| omc | 116s | 880k |
| codex | 192s | 767k |
| omx | 279s | 1.9M |

### SWE-bench (3 Hard tasks)

| Agent | Pass | Time |
|-------|------|------|
| claude | 3/3 | 377s |
| omc | pending | — |

Full results with token breakdown, cached tokens, and per-task details at the [live report](https://devswha.github.io/OpenBench/).

---

## Quick Start

```bash
# Install
uv sync --python 3.11

# Check environment
openbench doctor

# Run benchmarks
openbench run --agent claude --suite practical
openbench run --agent omc --suite practical
openbench run --agent codex --suite practical
openbench run --agent omx --suite practical

# SWE-bench (requires dataset download + Docker)
openbench fetch swe-bench
openbench run --agent claude --suite swe-bench

# Generate report
openbench report --format html --input results/<run-id>
```

## Commands

| Command | Description |
|---------|-------------|
| `openbench doctor` | Check environment readiness |
| `openbench list agents` | List registered agents |
| `openbench list suites` | List available suites |
| `openbench run --agent <name> --suite <name>` | Execute benchmark |
| `openbench fetch swe-bench` | Download SWE-bench Verified dataset |
| `openbench report --format html --input <dir>` | Generate HTML report |

---

## Benchmark Rules

Full specification: [docs/specs/benchmark-rules.md](docs/specs/benchmark-rules.md)

Key rules:
- **Same prompt** for all agents (neutral, no agent-specific optimization)
- **Hidden tests** — agents don't see test files; tests applied only during evaluation
- **5 runs per task** for statistical significance (Pass@1, Pass@5, Pass@5 strict)
- **Independent metrics** — correctness, duration, and token usage reported separately
- **Per-difficulty reporting** — Easy/Medium/Hard results shown independently

---

## Architecture

```
openbench/
├── agents/           # Agent adapters (claude, omc, codex, omx)
├── suites/
│   ├── runtime/      # CLI startup/memory/binary benchmarks
│   ├── practical/    # Self-contained fixture tasks
│   └── swebench/     # SWE-bench Verified integration
├── metrics/          # Statistics (Pass@1/5/strict) + result storage
├── reporters/        # HTML report generator
├── runner.py         # Execution engine
└── cli.py            # Click CLI
```

## Requirements

- Python **3.11+**
- [`uv`](https://docs.astral.sh/uv/) recommended
- `hyperfine`, GNU `time`, `du` (for runtime suite)
- `docker`, `git` (for SWE-bench suite)
- Agent CLIs installed: `claude`, `codex`, `omx`

## Development

```bash
uv sync --python 3.11 --extra dev
uv run ruff check .
uv run python -m pytest -q
```

61 tests, fixture-backed shim agents for CI without live API calls.

---

## License

MIT — see [`LICENSE`](./LICENSE).
