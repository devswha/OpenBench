from __future__ import annotations

import os

from openbench.agents.base import RuntimeCommandAgent


class OMXAgent(RuntimeCommandAgent):
    name = "omx"
    display_name = "oh-my-codex"
    command = "omx"

    def __init__(self, command: str | None = None) -> None:
        super().__init__(command=command or os.environ.get("OPENBENCH_OMX_COMMAND", self.command))

    def build_practical_command(self, resolved_command: str, task) -> list[str]:
        if task.metadata.get("environment_mode") == "containerized":
            return [
                resolved_command,
                task.prompt,
            ]
        return [
            resolved_command,
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C",
            str(task.workspace),
            task.prompt,
        ]
