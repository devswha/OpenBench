# OpenBench

**Open benchmarking framework for coding-agent CLIs.**

Same tasks. Same environment. Comparable results.

> **[Live Report](https://devswha.github.io/OpenBench/)** — interactive results with per-task token breakdown

---

## What's New

- **2026-04-13** — SWE-bench Verified integration: claude passes 3/3 Hard tasks (Django, Sympy)
- **2026-04-13** — Token tracking with input/cached/output breakdown for all 4 agents
- **2026-04-12** — First real benchmark run: claude, omc, codex, omx on 5 Practical tasks
- **2026-04-12** — Benchmark rules spec finalized: hidden tests, 5-run repetitions, per-difficulty reporting

---

## Latest Results

### Practical — 5 Easy tasks (all agents 5/5 pass)

| Agent | Type | Time | Tokens (in) | Tokens (out) |
|-------|------|------|-------------|-------------|
| **claude** | Claude Code (native) | **93s** | 834k | 2.4k |
| **omc** | Claude + OMC plugins | 116s | 880k | 2.8k |
| **codex** | Codex CLI (native) | 192s | 767k | 7.6k |
| **omx** | Codex + OMX wrapper | 279s | 1.9M | 10.4k |

### SWE-bench — 3 Hard tasks (real GitHub issues)

| Agent | Pass | Time | Tasks |
|-------|------|------|-------|
| **claude** | **3/3** | 377s | django-17087, django-16493, sympy-24213 |
| **omc** | 2/3 | 271s | pending re-run with patch fix |

> Wrapper overhead: OMC adds ~25% time vs native claude. OMX adds ~45% vs native codex.
> Token counts are normalized (input includes cached). See [live report](https://devswha.github.io/OpenBench/) for full breakdown.

---

## Benchmark Suites

| Suite | Tier | Tasks | What it tests |
|-------|------|-------|---------------|
| **Practical** | 0 | 5 self-contained fixtures | Bug fixes, feature additions, refactoring — fast CI validation |
| **[SWE-bench](https://github.com/swe-bench/SWE-bench)** | 1 | 50 curated [SWE-bench Verified](https://www.swebench.com/) issues | Production-grade coding on Django, Sympy, scikit-learn, matplotlib, Flask, Requests |
| **Runtime** | — | 3 CLI metrics | Startup latency, peak memory, binary size |

### About SWE-bench

[SWE-bench](https://github.com/swe-bench/SWE-bench) ([ICLR 2024 Oral](https://arxiv.org/abs/2310.06770)) is a benchmark for evaluating LLMs on real-world GitHub issues. Given a codebase and an issue description, the model generates a patch to resolve the problem.

OpenBench integrates **SWE-bench Verified** — a human-validated subset of 500 problems confirmed solvable by real software engineers ([report](https://openai.com/index/introducing-swe-bench-verified/)). We use the official Docker-based evaluation harness for reproducible per-instance evaluation, while adding **agent CLI comparison** (time, tokens, cache) on top of the standard pass/fail grading.

## Agents

| Agent | CLI | What it is |
|-------|-----|------------|
| `claude` | `claude -p` | [Claude Code](https://claude.ai/code) native — no plugins, no hooks |
| `omc` | `claude -p` | [oh-my-claudecode](https://github.com/anthropics/claude-code) — Claude Code + OMC orchestration layer |
| `codex` | `codex exec` | [OpenAI Codex CLI](https://github.com/openai/codex) native |
| `omx` | `omx exec` | [oh-my-codex](https://github.com/devswha/oh-my-codex) — Codex CLI + OMX wrapper |

---

## Quick Start

```bash
# Install
uv sync --python 3.11

# Check environment
openbench doctor

# Run practical benchmarks
openbench run --agent claude --suite practical
openbench run --agent codex --suite practical

# Run SWE-bench (requires dataset + Docker)
openbench fetch swe-bench
openbench run --agent claude --suite swe-bench

# Generate report
openbench report --format html --input results/<run-id>
```

> **Resource requirements for SWE-bench:** Docker (images 2-8 GB each), ~50 GB disk for 50 instances, 5-15 min per task, API costs vary by agent.

## CLI Reference

| Command | Description |
|---------|-------------|
| `openbench doctor` | Check environment readiness (agents, tools, Docker) |
| `openbench list agents` | List registered agents (`claude`, `omc`, `codex`, `omx`) |
| `openbench list suites` | List available suites (`practical`, `runtime`, `swe-bench`) |
| `openbench run --agent <a> --suite <s>` | Execute benchmark run |
| `openbench run --agent <a> --suite <s> --runs 5` | Execute with N repetitions |
| `openbench fetch swe-bench` | Download SWE-bench Verified dataset (500 instances) |
| `openbench report --format html --input <dir>` | Generate static HTML report |

---

## Benchmark Rules

Full specification: [docs/specs/benchmark-rules.md](docs/specs/benchmark-rules.md)

| Rule | Detail |
|------|--------|
| Prompting | Neutral task description, no agent-specific optimization |
| Tests | Hidden — applied only during evaluation, never shown to agents |
| Repetitions | 5 runs per task for statistical significance |
| Metrics | Pass@1, Pass@5, Pass@5 strict — per difficulty level |
| Token tracking | Input (normalized), cached, output — comparable across providers |
| Code quality | Not scored — pass/fail by automated tests only (no LLM judge) |

### How it compares to other benchmarks

| | OpenBench | [SWE-bench](https://github.com/SWE-bench/SWE-bench) | [Aider Polyglot](https://github.com/Aider-AI/polyglot-benchmark) |
|---|---|---|---|
| **Measures** | Agent CLI frameworks | Model capability | Model code generation |
| **Tasks** | Practical + SWE-bench | Real GitHub issues | Exercism problems (6 languages) |
| **Compares** | Claude Code vs Codex vs wrappers | Agents on fixed scaffold | Raw model output |
| **Tracks** | Correctness + time + tokens + cache | Correctness only | Correctness only |
| **Environment** | Same prompt, hidden tests, Docker | Docker per-instance | Docker sandbox |

---

## Architecture

```
openbench/
├── agents/              # Agent adapters (claude, omc, codex, omx)
│   ├── claude_native.py # Claude Code -p (native)
│   ├── omc.py           # oh-my-claudecode (with OMC hooks)
│   ├── codex_native.py  # Codex CLI exec (native)
│   └── omx.py           # oh-my-codex (with OMX wrapper)
├── suites/
│   ├── runtime/         # CLI startup / memory / binary benchmarks
│   ├── practical/       # Self-contained fixture tasks (Tier 0)
│   └── swebench/        # SWE-bench Verified integration (Tier 1)
├── metrics/
│   ├── statistics.py    # Pass@1, Pass@5, Pass@5 strict computation
│   └── store.py         # Result persistence (JSON per-agent per-suite)
├── reporters/
│   ├── html_reporter.py # Static HTML report with tabs + collapsible details
│   ├── parser.py        # JSON artifact → report model
│   └── models.py        # Report data models
├── runner.py            # Execution engine (task loop, workspace management)
└── cli.py               # Click CLI (run, report, fetch, doctor, list)
```

## Requirements

- Python **3.11+** with [`uv`](https://docs.astral.sh/uv/)
- `hyperfine`, GNU `time`, `du` — for runtime suite
- `docker`, `git` — for SWE-bench suite
- Agent CLIs: `claude` and/or `codex`/`omx`

## Development

```bash
uv sync --python 3.11 --extra dev
uv run ruff check .
uv run python -m pytest -q    # 61 tests
```

Tests use fixture-backed shim agents — no live API calls needed for CI.

---

## Acknowledgments

- [SWE-bench](https://github.com/swe-bench/SWE-bench) by Princeton NLP — the benchmark dataset and Docker evaluation harness that powers our Tier 1 suite
- [claw-bench](https://github.com/devswha/claw-bench) — predecessor project focused on CLI runtime overhead; OpenBench continues and expands this work into task-effectiveness benchmarking

## License

MIT — see [`LICENSE`](./LICENSE).
