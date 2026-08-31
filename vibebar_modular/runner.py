"""Process execution isolated behind a typed contract."""

from __future__ import annotations

import subprocess
from typing import Sequence

from .contracts import CommandResult


class SubprocessRunner:
    def run(self, arguments: Sequence[str]) -> CommandResult:
        completed = subprocess.run(
            list(arguments),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
