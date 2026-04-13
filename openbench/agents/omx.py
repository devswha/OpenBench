from __future__ import annotations

import os

from openbench.agents.base import RuntimeCommandAgent
from openbench.agents.codex_native import _parse_codex_jsonl
from openbench.models import TokenUsage


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
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C",
            str(task.workspace),
            task.prompt,
        ]

    def parse_token_usage(self, output: str) -> TokenUsage | None:
        usage = _parse_codex_jsonl(output)
        if not usage:
            return None
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            provider="openai",
        )

    def parse_agent_log(self, output: str) -> dict | None:
        usage = _parse_codex_jsonl(output)
        if not usage:
            return None
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cached_input_tokens": usage.get("cached_input_tokens", 0),
        }
