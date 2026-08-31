"""Windows implementation of the file-opening boundary."""

from __future__ import annotations

import os
from pathlib import Path

from vibebar_modular.contracts import CommandResult


class WindowsFileOpenerSocket:
    def open(self, path: Path) -> CommandResult:
        try:
            os.startfile(path)
        except OSError as error:
            return CommandResult(1, stderr=str(error))
        return CommandResult(0)
