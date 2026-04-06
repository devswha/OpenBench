from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator


class TempWorkspaceManager:
    def __init__(self, prefix: str = "openbench-") -> None:
        self.prefix = prefix

    @contextmanager
    def workspace(self) -> Iterator[Path]:
        with TemporaryDirectory(prefix=self.prefix) as directory:
            yield Path(directory)
