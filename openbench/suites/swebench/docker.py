"""Docker image management for SWE-bench evaluation."""
from __future__ import annotations

import shutil
from pathlib import Path

from openbench.utils.process import combine_output, run_subprocess


def image_name_for_instance(instance: dict) -> str:
    """Derive the SWE-bench Docker image tag from instance metadata."""
    instance_id = instance["instance_id"]
    # SWE-bench image format: swebench/sweb.eval.x86_64.<instance_id>:latest
    return f"swebench/sweb.eval.x86_64.{instance_id}:latest"


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

    completed = run_subprocess(
        [
            docker_bin, "run", "--rm",
            "-v", f"{workspace}:/testbed",
            "-w", "/testbed",
            image,
            "bash", "-c", test_command,
        ],
        timeout=timeout,
    )
    return combine_output(completed)
