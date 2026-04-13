from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class TempWorkspaceManager:
    def __init__(self, prefix: str = "openbench-") -> None:
        self.prefix = prefix

    @contextmanager
    def workspace(self) -> Iterator[Path]:
        directory = tempfile.mkdtemp(prefix=self.prefix)
        try:
            yield Path(directory)
        finally:
            shutil.rmtree(directory, ignore_errors=True)
