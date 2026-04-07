from __future__ import annotations

from openbench.reporters.models import ReportMetric


def test_report_metric_formats_values() -> None:
    metric = ReportMetric(
        key="startup_ms",
        label="Startup",
        unit="ms",
        raw_value=123.456,
        normalized_score=91.234,
        status="success",
        available=True,
    )

    assert metric.formatted_raw_value == "123.46 ms"
    assert metric.formatted_score == "91.23"


def test_report_metric_formats_unavailable_value() -> None:
    metric = ReportMetric(
        key="memory_mb",
        label="Memory",
        unit="MB",
        raw_value=None,
        normalized_score=None,
        status="failed",
        available=False,
        error_message="missing tool",
    )

    assert metric.formatted_raw_value == "Unavailable"
    assert metric.formatted_score == "—"


def test_report_metric_keeps_precision_for_tiny_mb_values() -> None:
    metric = ReportMetric(
        key="binary_size_mb",
        label="Binary size",
        unit="MB",
        raw_value=0.00005,
        normalized_score=100.0,
        status="success",
        available=True,
    )

    assert metric.formatted_raw_value == "0.00005 MB"
