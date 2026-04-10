from __future__ import annotations

from pathlib import Path

import click

from openbench.config import load_config
from openbench.containerization import docker_doctor_checks
from openbench.models import EnvironmentMode
from openbench.reporters import ReportInputError, StaticHtmlReporter, parse_runtime_report
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
@click.option(
    "--environment-mode",
    type=click.Choice([mode.value for mode in EnvironmentMode]),
    default=EnvironmentMode.NATIVE.value,
    show_default=True,
)
def doctor(config_path: Path | None, results_dir: Path | None, environment_mode: str) -> None:
    """Check environment readiness for the current MVP scope."""
    config = load_config(
        config_path=config_path,
        results_dir_override=results_dir,
        environment_mode_override=EnvironmentMode(environment_mode),
    )
    checks = []
    for agent_factory in AGENT_REGISTRY.values():
        checks.extend(agent_factory().doctor_checks())
    checks.extend(SUITE_REGISTRY["runtime"](config).doctor_checks())
    checks.extend(docker_doctor_checks(config))
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
@click.option(
    "--environment-mode",
    type=click.Choice([mode.value for mode in EnvironmentMode]),
    default=EnvironmentMode.NATIVE.value,
    show_default=True,
)
def run(
    agent_name: str,
    suite_name: str,
    config_path: Path | None,
    results_dir: Path | None,
    environment_mode: str,
) -> None:
    """Execute the MVP benchmark slice."""
    mode = EnvironmentMode(environment_mode)
    if mode == EnvironmentMode.CONTAINERIZED and suite_name != "practical":
        raise click.ClickException("Containerized mode is currently supported for the practical suite only")

    config = load_config(
        config_path=config_path,
        results_dir_override=results_dir,
        environment_mode_override=mode,
    )
    summary = Runner(config).run(agent_name, suite_name)

    click.echo(f"Run directory: {summary.run_dir}")
    click.echo(f"Manifest: {summary.manifest_path}")
    click.echo(f"Suite report: {summary.suite_report_path}")
    if summary.had_failures:
        click.echo("Run completed with task failures.")
        raise SystemExit(1)

    click.echo("Run completed successfully.")


@main.command()
@click.option("--format", "report_format", type=click.Choice(["html"]), default="html", show_default=True)
@click.option("--input", "input_dir", type=click.Path(path_type=Path, file_okay=False), required=True)
@click.option("--output", "output_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def report(report_format: str, input_dir: Path, output_path: Path | None) -> None:
    """Generate a static report from a saved runtime run directory."""
    try:
        parsed_run = parse_runtime_report(input_dir)
    except ReportInputError as exc:
        raise click.ClickException(str(exc)) from exc

    destination = output_path or input_dir / f"report.{report_format}"
    reporter_factories = {
        "html": StaticHtmlReporter,
    }
    reporter_factory = reporter_factories[report_format]
    reporter_factory().write(parsed_run.report, destination)
    click.echo(f"Report written: {destination}")


if __name__ == "__main__":
    main()
