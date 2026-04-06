from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any


@dataclass(slots=True)
class NormalizationReferences:
    startup_ms: float = 1000.0
    memory_mb: float = 512.0
    binary_size_mb: float = 100.0


@dataclass(slots=True)
class AppConfig:
    results_dir: Path = Path("results")
    normalization: NormalizationReferences = field(default_factory=NormalizationReferences)


def _coerce_float(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"Expected numeric value for normalization.{key}, got {value!r}")


def load_config(config_path: Path | None = None, results_dir_override: Path | None = None) -> AppConfig:
    resolved_config_path = config_path
    if resolved_config_path is None:
        candidate = Path("openbench.toml")
        resolved_config_path = candidate if candidate.exists() else None

    config_data: dict[str, Any] = {}
    if resolved_config_path is not None:
        config_data = tomllib.loads(resolved_config_path.read_text())

    normalization_data = config_data.get("normalization", {})
    normalization = NormalizationReferences(
        startup_ms=_coerce_float(normalization_data, "startup_ms", 1000.0),
        memory_mb=_coerce_float(normalization_data, "memory_mb", 512.0),
        binary_size_mb=_coerce_float(normalization_data, "binary_size_mb", 100.0),
    )

    configured_results_dir = config_data.get("results_dir", "results")
    if not isinstance(configured_results_dir, str):
        raise ValueError("Expected results_dir to be a string path")

    results_dir = results_dir_override or Path(configured_results_dir)
    return AppConfig(results_dir=results_dir, normalization=normalization)
