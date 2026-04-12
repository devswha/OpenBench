"""Statistical metrics for multi-run benchmark results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskRunResult:
    """A single run result for a task."""
    task_name: str
    run_index: int
    success: bool
    duration_ms: int | None = None
    total_tokens: int | None = None
    difficulty: str = "easy"
    category: str = "bugfix"


@dataclass(frozen=True, slots=True)
class TaskStats:
    """Aggregated statistics for a single task across N runs."""
    task_name: str
    difficulty: str
    category: str
    total_runs: int
    successful_runs: int
    pass_at_1: bool          # Was the first run successful?
    pass_at_n: bool          # Was at least 1 run successful?
    pass_at_n_strict: bool   # Were ALL runs successful?
    mean_duration_ms: float | None = None    # Mean duration of successful runs
    mean_tokens: float | None = None          # Mean tokens of successful runs


@dataclass(slots=True)
class DifficultyStats:
    """Aggregated statistics for a difficulty level across all tasks."""
    difficulty: str
    task_count: int = 0
    pass_at_1_rate: float = 0.0       # % of tasks where first run passed
    pass_at_n_rate: float = 0.0       # % of tasks where at least 1 run passed
    pass_at_n_strict_rate: float = 0.0  # % of tasks where all runs passed
    mean_tokens_per_success: float | None = None
    median_duration_per_success: float | None = None
    tasks: list[TaskStats] = field(default_factory=list)


@dataclass(slots=True)
class CategoryStats:
    """Pass@1 rate for a specific category within a difficulty level."""
    category: str
    difficulty: str
    task_count: int = 0
    pass_at_1_rate: float = 0.0


def compute_task_stats(runs: list[TaskRunResult]) -> TaskStats:
    """Compute stats for a single task from its N runs."""
    if not runs:
        raise ValueError("Cannot compute stats from empty run list")

    task_name = runs[0].task_name
    difficulty = runs[0].difficulty
    category = runs[0].category

    sorted_runs = sorted(runs, key=lambda r: r.run_index)
    successful = [r for r in sorted_runs if r.success]

    pass_at_1 = sorted_runs[0].success if sorted_runs else False
    pass_at_n = len(successful) > 0
    pass_at_n_strict = len(successful) == len(sorted_runs)

    # Duration/tokens only from successful runs
    durations = [r.duration_ms for r in successful if r.duration_ms is not None]
    tokens = [r.total_tokens for r in successful if r.total_tokens is not None]

    mean_duration = sum(durations) / len(durations) if durations else None
    mean_tokens = sum(tokens) / len(tokens) if tokens else None

    return TaskStats(
        task_name=task_name,
        difficulty=difficulty,
        category=category,
        total_runs=len(sorted_runs),
        successful_runs=len(successful),
        pass_at_1=pass_at_1,
        pass_at_n=pass_at_n,
        pass_at_n_strict=pass_at_n_strict,
        mean_duration_ms=mean_duration,
        mean_tokens=mean_tokens,
    )


def compute_difficulty_stats(task_stats_list: list[TaskStats], difficulty: str) -> DifficultyStats:
    """Compute aggregate stats for a difficulty level."""
    tasks = [t for t in task_stats_list if t.difficulty == difficulty]
    if not tasks:
        return DifficultyStats(difficulty=difficulty)

    count = len(tasks)
    pass_at_1_rate = sum(1 for t in tasks if t.pass_at_1) / count * 100
    pass_at_n_rate = sum(1 for t in tasks if t.pass_at_n) / count * 100
    pass_at_n_strict_rate = sum(1 for t in tasks if t.pass_at_n_strict) / count * 100

    # Tokens: mean across tasks that have token data
    token_values = [t.mean_tokens for t in tasks if t.mean_tokens is not None]
    mean_tokens = sum(token_values) / len(token_values) if token_values else None

    # Duration: median across tasks that have duration data
    duration_values = sorted([t.mean_duration_ms for t in tasks if t.mean_duration_ms is not None])
    if duration_values:
        mid = len(duration_values) // 2
        if len(duration_values) % 2 == 0:
            median_duration = (duration_values[mid - 1] + duration_values[mid]) / 2
        else:
            median_duration = duration_values[mid]
    else:
        median_duration = None

    return DifficultyStats(
        difficulty=difficulty,
        task_count=count,
        pass_at_1_rate=pass_at_1_rate,
        pass_at_n_rate=pass_at_n_rate,
        pass_at_n_strict_rate=pass_at_n_strict_rate,
        mean_tokens_per_success=mean_tokens,
        median_duration_per_success=median_duration,
        tasks=tasks,
    )


def compute_category_stats(task_stats_list: list[TaskStats]) -> list[CategoryStats]:
    """Compute Pass@1 by category within each difficulty level."""
    buckets: dict[tuple[str, str], list[TaskStats]] = {}
    for t in task_stats_list:
        key = (t.difficulty, t.category)
        buckets.setdefault(key, []).append(t)

    results = []
    for (difficulty, category), tasks in sorted(buckets.items()):
        count = len(tasks)
        rate = sum(1 for t in tasks if t.pass_at_1) / count * 100 if count else 0.0
        results.append(CategoryStats(
            category=category,
            difficulty=difficulty,
            task_count=count,
            pass_at_1_rate=rate,
        ))
    return results
