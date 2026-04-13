"""Download SWE-bench Verified dataset from HuggingFace."""
from __future__ import annotations

import json
from pathlib import Path


def fetch_swebench_verified(output_path: Path | None = None) -> Path:
    """Download SWE-bench Verified and write as instances.json.

    Requires the `datasets` package: pip install datasets
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is required for fetching SWE-bench data. "
            "Install it with: pip install datasets"
        ) from exc

    if output_path is None:
        output_path = Path(__file__).resolve().parents[3] / "tasks" / "swe-bench" / "instances.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset("SWE-bench/SWE-bench_Verified", split="test")

    instances = []
    for item in dataset:
        instances.append({
            "instance_id": item["instance_id"],
            "repo": item["repo"],
            "base_commit": item["base_commit"],
            "problem_statement": item["problem_statement"],
            "patch": item["patch"],
            "test_patch": item["test_patch"],
            "version": item.get("version", ""),
            "FAIL_TO_PASS": item.get("FAIL_TO_PASS", "[]"),
            "PASS_TO_PASS": item.get("PASS_TO_PASS", "[]"),
            "environment_setup_commit": item.get("environment_setup_commit", ""),
        })

    output_path.write_text(json.dumps(instances, indent=2))
    return output_path
