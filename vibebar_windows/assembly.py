"""Windows composition root; all business operations still use Legacy adapters."""

from __future__ import annotations

from pathlib import Path

from vibebar_modular.clock import SystemClock
from vibebar_modular.legacy import LegacyClipboardSocket, LegacyDigestSocket, LegacyEntrySocket, LegacyRecycleBin
from vibebar_modular.nulls import NullRecycleBin
from vibebar_modular.sockets import SocketSet

from .menu import WindowsMenuSocket
from .paths import discover
from .runner import WindowsBashRunner


def assemble_windows(
    repository: Path,
    environment: dict[str, str] | None = None,
    allow_deletion: bool = False,
) -> SocketSet:
    configured = _default_environment(repository)
    if environment is not None:
        configured.update(environment)
    runner = WindowsBashRunner(discover(repository), configured)
    recycle_bin = LegacyRecycleBin(repository, runner) if allow_deletion else NullRecycleBin()
    return SocketSet(
        entry=LegacyEntrySocket(repository, runner),
        clipboard=LegacyClipboardSocket(repository, runner),
        recycle_bin=recycle_bin,
        digest=LegacyDigestSocket(repository, runner),
        menu=WindowsMenuSocket(),
        clock=SystemClock(),
    )


def _default_environment(repository: Path) -> dict[str, str]:
    return {
        "VIBEBAR_FILE": str(Path.home() / "vibebar-journal.md"),
        "VIBEBAR_BUFFER": str(repository / "clipboard.txt"),
        "VIBEBAR_DIGEST_DIR": str(repository / "digests"),
        "VIBEBAR_AUTOPASTE": "0",
    }
