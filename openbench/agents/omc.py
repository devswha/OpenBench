from __future__ import annotations

import json
import os

from openbench.agents.base import RuntimeCommandAgent
from openbench.models import TokenUsage


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
            "--dangerously-skip-permissions",
            "--output-format", "json",
            task.prompt,
        ]

    def parse_token_usage(self, output: str) -> TokenUsage | None:
        try:
            data = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return None
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return None
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=data.get("total_cost_usd"),
            provider="anthropic",
        )

    def parse_agent_log(self, output: str) -> dict | None:
        try:
            data = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return None
        usage = data.get("usage", {})
        return {
            "num_turns": data.get("num_turns"),
            "duration_api_ms": data.get("duration_api_ms"),
            "cost_usd": data.get("total_cost_usd"),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "model_usage": data.get("modelUsage"),
        }
