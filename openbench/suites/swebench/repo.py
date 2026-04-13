"""Git repository management for SWE-bench tasks."""
from __future__ import annotations

import subprocess
from pathlib import Path

from openbench.utils.process import combine_output, run_subprocess


def clone_and_checkout(
    *,
    repo: str,
    base_commit: str,
    workspace: Path,
    timeout: int = 300,
) -> None:
    """Clone a GitHub repo and checkout a specific commit."""
    repo_url = f"https://github.com/{repo}.git"
    completed = run_subprocess(
        ["git", "clone", "--quiet", repo_url, str(workspace)],
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git clone failed: {combine_output(completed)}")

    completed = run_subprocess(
        ["git", "checkout", "--quiet", base_commit],
        cwd=workspace,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git checkout failed: {combine_output(completed)}")


def apply_patch(
    *,
    workspace: Path,
    patch_content: str,
    timeout: int = 30,
) -> None:
    """Apply a git patch to the workspace.

    If --3way fails (agent modified the same files), reset conflicting
    files to base_commit and retry with a plain apply.
    """
    completed = subprocess.run(
        ["git", "apply", "--3way", "-"],
        cwd=str(workspace),
        input=patch_content.encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode == 0:
        return

    # Extract conflicting file paths from the patch and reset them
    conflicting_files = _extract_patch_paths(patch_content)
    if conflicting_files:
        subprocess.run(
            ["git", "checkout", "HEAD", "--"] + conflicting_files,
            cwd=str(workspace),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        # Retry with plain apply
        retry = subprocess.run(
            ["git", "apply", "-"],
            cwd=str(workspace),
            input=patch_content.encode(),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if retry.returncode == 0:
            return

    stderr = completed.stderr.decode(errors="replace").strip()
    stdout = completed.stdout.decode(errors="replace").strip()
    output = "\n".join(part for part in [stdout, stderr] if part).strip()
    raise RuntimeError(f"git apply failed: {output}")


def _extract_patch_paths(patch_content: str) -> list[str]:
    """Extract file paths from a unified diff patch."""
    paths = []
    for line in patch_content.splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[6:])
    return paths
