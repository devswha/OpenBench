from openbench.metrics.statistics import (
    TaskRunResult,
    compute_task_stats,
    compute_difficulty_stats,
    compute_category_stats,
)


def test_compute_task_stats_all_pass():
    runs = [
        TaskRunResult("task-a", 0, True, 5000, 1500, "easy", "bugfix"),
        TaskRunResult("task-a", 1, True, 6000, 1600, "easy", "bugfix"),
        TaskRunResult("task-a", 2, True, 5500, 1550, "easy", "bugfix"),
    ]
    stats = compute_task_stats(runs)
    assert stats.pass_at_1 is True
    assert stats.pass_at_n is True
    assert stats.pass_at_n_strict is True
    assert stats.successful_runs == 3
    assert stats.mean_duration_ms is not None
    assert abs(stats.mean_duration_ms - 5500.0) < 1


def test_compute_task_stats_partial_pass():
    runs = [
        TaskRunResult("task-b", 0, False, 8000, 2000, "medium", "feature"),
        TaskRunResult("task-b", 1, True, 6000, 1800, "medium", "feature"),
        TaskRunResult("task-b", 2, False, 9000, 2200, "medium", "feature"),
    ]
    stats = compute_task_stats(runs)
    assert stats.pass_at_1 is False
    assert stats.pass_at_n is True
    assert stats.pass_at_n_strict is False
    assert stats.successful_runs == 1


def test_compute_task_stats_all_fail():
    runs = [
        TaskRunResult("task-c", 0, False, difficulty="hard", category="debug"),
        TaskRunResult("task-c", 1, False, difficulty="hard", category="debug"),
    ]
    stats = compute_task_stats(runs)
    assert stats.pass_at_1 is False
    assert stats.pass_at_n is False
    assert stats.pass_at_n_strict is False
    assert stats.mean_duration_ms is None
    assert stats.mean_tokens is None


def test_compute_difficulty_stats():
    from openbench.metrics.statistics import TaskStats
    tasks = [
        TaskStats("t1", "easy", "bugfix", 5, 5, True, True, True, 5000.0, 1500.0),
        TaskStats("t2", "easy", "feature", 5, 3, True, True, False, 6000.0, 1800.0),
        TaskStats("t3", "easy", "bugfix", 5, 0, False, False, False, None, None),
    ]
    ds = compute_difficulty_stats(tasks, "easy")
    assert ds.task_count == 3
    assert abs(ds.pass_at_1_rate - 66.67) < 1
    assert abs(ds.pass_at_n_rate - 66.67) < 1
    assert abs(ds.pass_at_n_strict_rate - 33.33) < 1


def test_compute_category_stats():
    from openbench.metrics.statistics import TaskStats
    tasks = [
        TaskStats("t1", "easy", "bugfix", 5, 5, True, True, True),
        TaskStats("t2", "easy", "bugfix", 5, 0, False, False, False),
        TaskStats("t3", "easy", "feature", 5, 5, True, True, True),
    ]
    cats = compute_category_stats(tasks)
    bugfix = next(c for c in cats if c.category == "bugfix" and c.difficulty == "easy")
    feature = next(c for c in cats if c.category == "feature" and c.difficulty == "easy")
    assert bugfix.pass_at_1_rate == 50.0
    assert feature.pass_at_1_rate == 100.0
