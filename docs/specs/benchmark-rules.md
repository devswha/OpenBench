# OpenBench Benchmark Rules & Environment Specification

> Ratified: 2026-04-12
> Status: Active

## 1. Environment

| Item | Decision |
|------|----------|
| Execution | Docker containers (controlled, reproducible) |
| Base image | Python 3.11-slim-bookworm |
| Agent installation | Real CLIs installed in container (npm install) |
| API keys | Injected as environment variables at runtime |
| Network | Allowed (required for API calls) |
| CPU/Memory limits | None (bottleneck is API server, not local compute) |
| Package installation | Forbidden during task execution |

## 2. Evaluation Rules

| Item | Decision |
|------|----------|
| Repetitions | 5 runs per task per agent |
| Timeout | Safety-only (600s), not a scoring factor |
| Test visibility | **Hidden** — tests are applied only during evaluation |
| Success criteria | Automated test pass/fail |
| Reporting metric | **Success rate** (N/5) |
| Duration | Recorded but not scored — informational only |
| Token usage | Recorded but not scored — informational only |

## 3. Prompting Rules

### What the agent receives
- A neutral, task-only description (no hints, no "think step by step")
- List of editable files (if applicable)
- Success criteria description (without revealing test code)

### What the agent does NOT receive
- Test files or test code
- Gold solution or reference patch
- Agent-specific optimized instructions

### Agent freedom
| Item | Decision |
|------|----------|
| Built-in capabilities (tool use, file read) | Allowed |
| System prompt | Agent defaults (as shipped) |
| Self-retry loops | Allowed (agent may test and fix iteratively) |
| Web search | Forbidden |
| Package installation | Forbidden |

### Prompt format (template)

```
You are given a project in the current working directory.

## Task
{task_description}

## Editable files
{file_list or "Any file in the repository"}

## Constraints
- Only modify files listed as editable above (if specified)
- Do not install additional packages
- Your changes will be validated by automated tests (not shown)
```

For SWE-bench tasks, the prompt is the original GitHub issue `problem_statement` as-is.

## 4. Task Structure

### Tiers

| Tier | Source | Purpose | Count |
|------|--------|---------|-------|
| Tier 0 | Self-contained fixtures | CI / quick validation | 5 |
| Tier 1 | SWE-bench Verified subset | Official benchmark | ~50 |
| Tier 2 | Terminal-Bench (future) | CLI agent evaluation | TBD |

### Difficulty levels
- **Easy** — single file, obvious problem, small change
- **Medium** — multi-file, requires context understanding
- **Hard** — complex logic, design decisions required

### Categories
- **Bug Fix** — find and fix bugs in existing code
- **Feature** — add new functionality
- **Refactor** — restructure without changing behavior
- **Debug** — trace from error output to root cause
- **Test** — write tests for existing code

### Fixture structure (Tier 0)

```
fixtures/{task-id}/
├── workspace/          # Given to agent
│   └── {source files}
└── evaluation/         # Hidden, used after agent finishes
    └── {test files}
```

### SWE-bench structure (Tier 1)

Each task uses the SWE-bench Docker image with the repository checked out at `base_commit`. After the agent finishes, the `test_patch` is applied and tests are run.

## 5. Scoring

All metrics are reported **per difficulty level** (Easy / Medium / Hard). There is no weighted composite score — each difficulty stands on its own.

### Per-difficulty metrics

| Metric | Definition | Purpose |
|--------|-----------|---------|
| **Pass@1** | Success rate on first attempt across tasks | Real-world user experience |
| **Pass@5** | At least 1 success in 5 attempts | Potential capability |
| **Pass@5 strict** | All 5 attempts succeed | Reliability / consistency |
| **Tokens/success** | Mean total tokens across successful runs | Cost efficiency |
| **Duration/success** | Median wall-clock time across successful runs | Speed |

### Report layout

```
┌─ Easy ──────────────────────────────────────────┐
│ Metric              │ omc        │ omx          │
│ Pass@1              │ 95%        │ 90%          │
│ Pass@5              │ 100%       │ 100%         │
│ Pass@5 strict       │ 80%        │ 75%          │
│ Tokens/success      │ 1,800      │ 1,200        │
│ Duration/success    │ 8.2s       │ 5.1s         │
└─────────────────────────────────────────────────┘

┌─ Medium ────────────────────────────────────────┐
│ Metric              │ omc        │ omx          │
│ Pass@1              │ 65%        │ 70%          │
│ Pass@5              │ 85%        │ 80%          │
│ Pass@5 strict       │ 30%        │ 40%          │
│ Tokens/success      │ 5,400      │ 3,800        │
│ Duration/success    │ 45.3s      │ 32.1s        │
└─────────────────────────────────────────────────┘

┌─ Hard ──────────────────────────────────────────┐
│ Metric              │ omc        │ omx          │
│ Pass@1              │ 30%        │ 20%          │
│ Pass@5              │ 55%        │ 40%          │
│ Pass@5 strict       │ 5%         │ 0%           │
│ Tokens/success      │ 12,000     │ 8,500        │
│ Duration/success    │ 120.5s     │ 95.2s        │
└─────────────────────────────────────────────────┘
```

### Supplementary views

- **Category heatmap**: Pass@1 broken down by category (Bug Fix / Feature / Refactor / Debug / Test) within each difficulty — reveals per-agent strengths and weaknesses
- **Per-task detail**: individual task results for full transparency

### Explicitly excluded

- **Code quality scoring** — no LLM judge. The pass/fail criterion is automated test results only. Reasons: LLM judges introduce bias (e.g., Claude judging Claude Code), subjective criteria reduce reproducibility, and the metric is not deterministic across runs.

## 6. Fairness Guarantees

1. **Same prompt**: all agents receive identical task descriptions
2. **Same environment**: all agents run in identical Docker containers
3. **Same evaluation**: same hidden tests applied to all agents
4. **No optimization**: prompts are not tuned for any specific agent
5. **Statistical significance**: 5 runs per task to account for LLM non-determinism
