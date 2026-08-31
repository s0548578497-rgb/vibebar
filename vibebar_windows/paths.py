"""Discover Windows dependencies without machine-specific constants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


@dataclass(frozen=True, slots=True)
class WindowsPaths:
    repository: Path
    bash: Path
    python: Path
    shims: Path


def discover(repository: Path) -> WindowsPaths:
    bash = _find_git_bash()
    return WindowsPaths(
        repository=repository.resolve(),
        bash=bash,
        python=Path(sys.executable).resolve(),
        shims=(repository / "windows" / "bin").resolve(),
    )


def _find_git_bash() -> Path:
    candidates = (
        Path("C:/Program Files/Git/bin/bash.exe"),
        Path("C:/Program Files/Git/usr/bin/bash.exe"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    located = shutil.which("bash.exe")
    if located is None or "system32" in located.casefold():
        raise FileNotFoundError("Git Bash is required for the Windows adapter")
    return Path(located)
