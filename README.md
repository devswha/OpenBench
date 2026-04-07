# OpenBench

**Open benchmarking framework for coding-agent CLIs.**

OpenBench exists to measure coding-agent tools in a way that is:

- **comparable** — same suite, same machine, same output shape
- **reproducible** — versioned manifests and persisted result files
- **incremental** — start with stable runtime benchmarks, expand later to harder task suites

The current repository is intentionally focused on a **Phase 1 runtime-benchmark MVP**.

---

## Benchmark Purpose

OpenBench is trying to answer questions like:

- How fast does each coding-agent CLI start?
- How much memory does it consume for a minimal invocation?
- What is the on-disk footprint of the installed command entrypoint?
- Can we persist those measurements in a clean, machine-readable format for later comparison?

This MVP does **not** yet benchmark prompt quality, repo-editing quality, or orchestration success. It benchmarks the **runtime surface first** so the harness, persistence model, and verification flow are solid before broader capability claims are made.

---

## Current Benchmark Coverage

### Implemented now

- **Agents:** `omc`, `omx`
- **Suite:** `runtime`
- **Commands:** `run`, `list`, `doctor`, `report`
- **Artifacts:** `manifest.json`, per-agent `runtime.json`, and static `report.html`

### Not implemented yet

- `omo`
- task-completion benchmarks
- orchestration benchmarks
- `compare`
- richer leaderboard/report variants beyond the current static HTML report
- LLM-judge scoring
- Docker isolation

---

## Current Progress

OpenBench is currently at the **“runtime harness working”** stage.

What is already true:

- local runtime benchmarking works for `omc`
- local runtime benchmarking works for `omx`
- results are persisted under timestamped run directories
- static HTML reports can be generated from saved runtime runs
- tests and smoke checks run without requiring live external accounts

What is next:

1. expand adapter coverage
2. improve packaged-data handling for suite definitions
3. add task-completion benchmarks
4. add orchestration benchmarks
5. add reporting/comparison workflows

---

## Latest Published Runtime Snapshot — 2026-04-07

Published report:

- `https://devswha.github.io/OpenBench/`

These are **local validation snapshots from this machine**, not broad public benchmark claims.

| Agent | Startup (`--version`) | Peak memory | Binary path size |
|------|------------------------|-------------|------------------|
| `omc` | 127.35 ms | 192.38 MB | 49 bytes* |
| `omx` | 162.13 ms | 61.99 MB | 47 bytes* |

\* Current MVP measures the resolved command path size (`du -sb $(which <command>)`), which may reflect a launcher/wrapper rather than total installation footprint.

These runs were persisted successfully with:

- `manifest.json`
- `omc/runtime.json`
- `omx/runtime.json`

---

## What the `runtime` Suite Measures

The runtime suite currently uses three deterministic checks:

- **startup** — `hyperfine` around `<agent> --version`
- **memory** — GNU `time -v` around `<agent> --version`
- **binary-size** — `du -sb` on the resolved command path

So the MVP currently measures **CLI launch/runtime overhead**, not full task-solving performance.

Saved runtime runs can also be turned into a static report with:

- **report** — `openbench report --format html --input <run-dir>`

---

## Result Format

Each run writes a timestamped directory like:

```text
results/
└── 2026-04-06T08-13-09-506228Z/
    ├── manifest.json
    ├── report.html
    ├── omc/
    │   └── runtime.json
    └── omx/
        └── runtime.json
```

- `manifest.json` stores environment, version, and normalization metadata
- `<agent>/runtime.json` stores raw per-task measurements and normalized scores

---

## Requirements

- Python **3.11+**
- [`uv`](https://docs.astral.sh/uv/) recommended
- `hyperfine`
- GNU `time` with `-v`
- `du`
- installed agent CLIs for the adapters you want to benchmark

Current adapter-to-command mapping:

- `omc` → `claude`
- `omx` → `omx`

Optional overrides:

- `OPENBENCH_OMC_COMMAND`
- `OPENBENCH_OMX_COMMAND`
- `OPENBENCH_HYPERFINE_BIN`
- `OPENBENCH_TIME_BIN`
- `OPENBENCH_DU_BIN`

---

## Quick Start

```bash
uv sync --python 3.11 --extra dev

uv run --python 3.11 python -m openbench.cli doctor
uv run --python 3.11 python -m openbench.cli list agents
uv run --python 3.11 python -m openbench.cli list suites

uv run --python 3.11 python -m openbench.cli run --agent omc --suite runtime
uv run --python 3.11 python -m openbench.cli run --agent omx --suite runtime
uv run --python 3.11 python -m openbench.cli report --format html --input ./results/<run-id>
```

If you prefer the installed console script:

```bash
openbench doctor
openbench list agents
openbench list suites
openbench run --agent omc --suite runtime
openbench run --agent omx --suite runtime
openbench report --format html --input ./results/<run-id>
```

---

## Command Summary

### `doctor`

Checks whether the current machine is benchmark-ready:

- agent command presence
- `hyperfine`
- GNU `time`
- `du`

### `list`

Lists registered agents and suites:

```bash
openbench list agents
openbench list suites
```

### `run`

Runs one agent against one suite:

```bash
openbench run --agent omc --suite runtime --results-dir ./results
```

### `report`

Generates a static HTML report from a saved runtime run:

```bash
openbench report --format html --input ./results/<run-id> --output ./results/<run-id>/report.html
```

---

## Development / Verification

```bash
uv run --python 3.11 ruff check .
uv run --python 3.11 python -m pytest -q
```

The test suite includes fixture-backed shim binaries under `tests/fixtures/bin/` so CI and local verification can run without live network-backed agent execution.

---

## Roadmap

Planned after the runtime MVP:

1. add more adapters
2. add task-completion suites
3. add orchestration suites
4. improve packaged-data handling for suite definitions
5. add report/comparison workflows

---

## License

MIT — see [`LICENSE`](./LICENSE).
