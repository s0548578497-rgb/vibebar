"""Run original Bash adapters with Windows-native dependencies injected."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Sequence

from vibebar_modular.contracts import CommandResult

from .paths import WindowsPaths


PATH_VARIABLES = (
    "VIBEBAR_FILE",
    "VIBEBAR_DIGEST_DIR",
    "VIBEBAR_VAULT_FILE",
    "VIBEBAR_BUFFER",
    "SW_RECORDINGS",
)


@dataclass(frozen=True, slots=True)
class WindowsBashRunner:
    paths: WindowsPaths
    environment: dict[str, str] | None = None

    def run(self, arguments: Sequence[str]) -> CommandResult:
        converted = tuple(_to_git_path(value) for value in arguments)
        environment = os.environ.copy()
        if self.environment is not None:
            environment.update(self.environment)
        for name in PATH_VARIABLES:
            if environment.get(name):
                environment[name] = _to_git_path(environment[name])
        environment["VIBEBAR_PYTHON"] = _to_git_path(str(self.paths.python))
        environment["VIBEBAR_WINDOWS_ROOT"] = _to_git_path(str(self.paths.repository))
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        git_root = self.paths.bash.parent.parent
        path_parts = (
            str(self.paths.shims),
            str(git_root / "usr" / "bin" / "core_perl"),
            str(git_root / "usr" / "bin"),
            str(git_root / "bin"),
            environment.get("PATH", ""),
        )
        environment["PATH"] = ";".join(path_parts)
        completed = subprocess.run(
            [str(self.paths.bash), *converted],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _to_git_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute() or path.drive == "":
        return value
    drive = path.drive[0].casefold()
    tail = path.as_posix().split(":", 1)[1]
    return f"/{drive}{tail}"
