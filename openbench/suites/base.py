from __future__ import annotations

from abc import ABC, abstractmethod

from openbench.config import AppConfig
from openbench.models import DoctorCheck, RunResult, Score, Task


class BenchSuite(ABC):
    name: str
    tier: int
    description: str

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    @abstractmethod
    def load_tasks(self) -> list[Task]:
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, result: RunResult, agent_name: str) -> Score:
        raise NotImplementedError

    def doctor_checks(self) -> list[DoctorCheck]:
        return []
