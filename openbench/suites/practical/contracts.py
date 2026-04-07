from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PracticalTaskContract:
    identifier: str
    description: str
    fixture: Path
    allowed_touchpoints: list[str]
    success_command: str
    regression_command: str
    timeout: int
