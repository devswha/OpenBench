from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any

from openbench.models import EnvironmentMode


@dataclass(slots=True)
class NormalizationReferences:
    startup_ms: float = 1000.0
    memory_mb: float = 512.0
    binary_size_mb: float = 100.0


@dataclass(slots=True)
class AppConfig:
    results_dir: Path = Path("results")
    normalization: NormalizationReferences = field(default_factory=NormalizationReferences)
    environment_mode: EnvironmentMode = EnvironmentMode.NATIVE
    container_base_image: str = "openbench-practical-base:phase2b"
    container_image_prefix: str = "openbench-practical"
    container_docker_dir: Path = Path("docker/practical")


def _coerce_float(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"Expected numeric value for normalization.{key}, got {value!r}")


def _coerce_environment_mode(value: Any) -> EnvironmentMode:
    if isinstance(value, EnvironmentMode):
        return value
    if isinstance(value, str):
        try:
            return EnvironmentMode(value)
        except ValueError as exc:
            raise ValueError(f"Unknown environment mode: {value!r}") from exc
    raise ValueError(f"Expected environment mode to be a string, got {value!r}")


def load_config(
    config_path: Path | None = None,
    results_dir_override: Path | None = None,
    environment_mode_override: EnvironmentMode | None = None,
) -> AppConfig:
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

    execution_data = config_data.get("execution", {})
    if execution_data and not isinstance(execution_data, dict):
        raise ValueError("Expected execution config section to be a table/object")

    results_dir = results_dir_override or Path(configured_results_dir)
    environment_mode = environment_mode_override or _coerce_environment_mode(
        execution_data.get("mode", EnvironmentMode.NATIVE.value)
    )

    container_base_image = execution_data.get("container_base_image", "openbench-practical-base:phase2b")
    if not isinstance(container_base_image, str):
        raise ValueError("Expected execution.container_base_image to be a string")

    container_image_prefix = execution_data.get("container_image_prefix", "openbench-practical")
    if not isinstance(container_image_prefix, str):
        raise ValueError("Expected execution.container_image_prefix to be a string")

    container_docker_dir = execution_data.get("container_docker_dir", "docker/practical")
    if not isinstance(container_docker_dir, str):
        raise ValueError("Expected execution.container_docker_dir to be a string path")

    return AppConfig(
        results_dir=results_dir,
        normalization=normalization,
        environment_mode=environment_mode,
        container_base_image=container_base_image,
        container_image_prefix=container_image_prefix,
        container_docker_dir=Path(container_docker_dir),
    )
