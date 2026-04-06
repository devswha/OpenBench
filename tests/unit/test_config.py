from __future__ import annotations

from pathlib import Path

from openbench.config import load_config


def test_load_config_reads_results_dir_and_normalization(tmp_path: Path) -> None:
    config_path = tmp_path / "openbench.toml"
    config_path.write_text(
        "results_dir = 'custom-results'\n[normalization]\nstartup_ms = 50\nmemory_mb = 64\nbinary_size_mb = 10\n"
    )

    config = load_config(config_path=config_path)

    assert config.results_dir == Path("custom-results")
    assert config.normalization.startup_ms == 50.0
    assert config.normalization.memory_mb == 64.0
    assert config.normalization.binary_size_mb == 10.0
