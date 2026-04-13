from __future__ import annotations

from openbench.agents.claude_native import ClaudeNativeAgent
from openbench.agents.codex_native import CodexNativeAgent
from openbench.agents.omc import OMCAgent
from openbench.agents.omx import OMXAgent
from openbench.suites.practical.suite import PracticalTaskSuite
from openbench.suites.runtime.suite import RuntimeSuite
from openbench.suites.swebench.suite import SweBenchSuite


AGENT_REGISTRY = {
    OMCAgent.name: OMCAgent,
    OMXAgent.name: OMXAgent,
    ClaudeNativeAgent.name: ClaudeNativeAgent,
    CodexNativeAgent.name: CodexNativeAgent,
}

SUITE_REGISTRY = {
    PracticalTaskSuite.name: PracticalTaskSuite,
    RuntimeSuite.name: RuntimeSuite,
    SweBenchSuite.name: SweBenchSuite,
}


def list_agents() -> list[str]:
    return sorted(AGENT_REGISTRY)


def list_suites() -> list[str]:
    return sorted(SUITE_REGISTRY)
