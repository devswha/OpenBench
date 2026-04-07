from __future__ import annotations

from openbench.agents.omc import OMCAgent
from openbench.agents.omx import OMXAgent
from openbench.suites.practical.suite import PracticalTaskSuite
from openbench.suites.runtime.suite import RuntimeSuite


AGENT_REGISTRY = {
    OMCAgent.name: OMCAgent,
    OMXAgent.name: OMXAgent,
}

SUITE_REGISTRY = {
    PracticalTaskSuite.name: PracticalTaskSuite,
    RuntimeSuite.name: RuntimeSuite,
}


def list_agents() -> list[str]:
    return sorted(AGENT_REGISTRY)


def list_suites() -> list[str]:
    return sorted(SUITE_REGISTRY)
