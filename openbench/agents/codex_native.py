from __future__ import annotations

import os

from openbench.agents.base import RuntimeCommandAgent


class CodexNativeAgent(RuntimeCommandAgent):
    name = "codex"
    display_name = "Codex CLI (native)"
    command = "codex"

    def __init__(self, command: str | None = None) -> None:
        super().__init__(command=command or os.environ.get("OPENBENCH_CODEX_COMMAND", self.command))

    def build_practical_command(self, resolved_command: str, task) -> list[str]:
        return [
            resolved_command,
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C",
            str(task.workspace),
            task.prompt,
        ]
