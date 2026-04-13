"""Docker image management for SWE-bench evaluation."""
from __future__ import annotations

import shutil
from pathlib import Path

from openbench.utils.process import combine_output, run_subprocess


def image_name_for_instance(instance: dict) -> str:
    """Derive the SWE-bench Docker image tag from instance metadata."""
    instance_id = instance["instance_id"]
    # Epoch AI hosts all SWE-bench Verified images on GHCR
    return f"ghcr.io/epoch-research/swe-bench.eval.x86_64.{instance_id}:latest"


def ensure_image(instance: dict) -> str:
    """Pull SWE-bench Docker image if not present. Returns image name."""
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        raise RuntimeError("docker is not installed or not on PATH")

    image = image_name_for_instance(instance)

    # Check if image exists locally
    check = run_subprocess(
        [docker_bin, "image", "inspect", image, "--format", "{{.Id}}"],
        timeout=30,
    )
    if check.returncode == 0:
        return image

    # Pull from Docker Hub
    pull = run_subprocess(
        [docker_bin, "pull", image],
        timeout=600,
    )
    if pull.returncode != 0:
        raise RuntimeError(f"Failed to pull {image}: {combine_output(pull)}")

    return image


def run_tests_in_container(
    *,
    image: str,
    workspace: Path,
    test_command: str,
    timeout: int = 300,
) -> str:
    """Run test command inside SWE-bench container. Returns combined output."""
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        raise RuntimeError("docker is not installed or not on PATH")

    # SWE-bench images have the repo at /testbed but not pip-installed.
    # Mount the agent's workspace at /patch, copy into /testbed,
    # install dependencies, then run tests.
    copy_install_test = (
        "cp -r /patch/. /testbed/ 2>/dev/null; "
        "cd /testbed && pip install -e . --quiet 2>/dev/null; "
        f"{test_command}"
    )
    completed = run_subprocess(
        [
            docker_bin, "run", "--rm",
            "-v", f"{workspace}:/patch:ro",
            image,
            "bash", "-c", copy_install_test,
        ],
        timeout=timeout,
    )
    return combine_output(completed)
