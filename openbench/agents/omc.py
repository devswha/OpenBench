from __future__ import annotations

import os

from openbench.agents.base import RuntimeCommandAgent


class OMCAgent(RuntimeCommandAgent):
    name = "omc"
    display_name = "oh-my-claudecode"
    command = "claude"

    def __init__(self, command: str | None = None) -> None:
        super().__init__(command=command or os.environ.get("OPENBENCH_OMC_COMMAND", self.command))

    def build_practical_command(self, resolved_command: str, task) -> list[str]:
        return [
            resolved_command,
            "-p",
            "--bare",
            "--dangerously-skip-permissions",
            task.prompt,
        ]
