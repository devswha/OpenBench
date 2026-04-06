from __future__ import annotations

from pathlib import Path

import click

from openbench.config import load_config
from openbench.registry import AGENT_REGISTRY, SUITE_REGISTRY, list_agents, list_suites
from openbench.runner import Runner


@click.group()
def main() -> None:
    """OpenBench command-line interface."""


@main.group(name="list")
def list_group() -> None:
    """List available agents and suites."""


@list_group.command(name="agents")
def list_agents_command() -> None:
    for agent_name in list_agents():
        click.echo(agent_name)


@list_group.command(name="suites")
def list_suites_command() -> None:
    for suite_name in list_suites():
        click.echo(suite_name)


@main.command()
@click.option("--config", "config_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--results-dir", type=click.Path(path_type=Path, file_okay=False), default=None)
def doctor(config_path: Path | None, results_dir: Path | None) -> None:
    """Check environment readiness for the current MVP scope."""
    config = load_config(config_path=config_path, results_dir_override=results_dir)
    checks = []
    for agent_factory in AGENT_REGISTRY.values():
        checks.extend(agent_factory().doctor_checks())
    checks.extend(SUITE_REGISTRY["runtime"](config).doctor_checks())
    all_ok = True
    for check in checks:
        status = "OK" if check.ok else "FAIL"
        click.echo(f"[{status}] {check.category}:{check.name} - {check.details}")
        all_ok = all_ok and check.ok

    if all_ok:
        click.echo("Environment ready.")
        return

    click.echo("Environment not ready.")
    raise SystemExit(1)


@main.command()
@click.option("--agent", "agent_name", required=True, type=click.Choice(list(AGENT_REGISTRY.keys())))
@click.option("--suite", "suite_name", required=True, type=click.Choice(list(SUITE_REGISTRY.keys())))
@click.option("--config", "config_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--results-dir", type=click.Path(path_type=Path, file_okay=False), default=None)
def run(agent_name: str, suite_name: str, config_path: Path | None, results_dir: Path | None) -> None:
    """Execute the MVP benchmark slice."""
    config = load_config(config_path=config_path, results_dir_override=results_dir)
    summary = Runner(config).run(agent_name, suite_name)

    click.echo(f"Run directory: {summary.run_dir}")
    click.echo(f"Manifest: {summary.manifest_path}")
    click.echo(f"Suite report: {summary.suite_report_path}")
    if summary.had_failures:
        click.echo("Run completed with task failures.")
        raise SystemExit(1)

    click.echo("Run completed successfully.")


if __name__ == "__main__":
    main()
