from __future__ import annotations

import os

from openbench.agents.base import RuntimeCommandAgent


class OMXAgent(RuntimeCommandAgent):
    name = "omx"
    display_name = "oh-my-codex"
    command = "omx"

    def __init__(self, command: str | None = None) -> None:
        super().__init__(command=command or os.environ.get("OPENBENCH_OMX_COMMAND", self.command))
