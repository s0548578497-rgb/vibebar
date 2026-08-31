"""The single composition root for selecting socket implementations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .clock import SystemClock
from .contracts import ClipboardSocket, Clock, DigestSocket, EntrySocket, FileOpenerSocket, MenuSocket, RecycleBinSocket
from .legacy import LegacyClipboardSocket, LegacyDigestSocket, LegacyEntrySocket, LegacyFileOpenerSocket, LegacyMenuSocket, LegacyRecycleBin
from .nulls import NullClipboardSocket, NullDigestSocket, NullEntrySocket, NullFileOpenerSocket, NullMenuSocket, NullRecycleBin
from .runner import SubprocessRunner


@dataclass(frozen=True, slots=True)
class SocketSet:
    entry: EntrySocket
    clipboard: ClipboardSocket
    recycle_bin: RecycleBinSocket
    digest: DigestSocket
    menu: MenuSocket
    opener: FileOpenerSocket
    clock: Clock


def build_sockets(root: Path, mode: str = "identity", allow_deletion: bool = False) -> SocketSet:
    if mode == "sealed":
        return _sealed_sockets()
    if mode != "identity":
        raise ValueError(f"unknown socket mode: {mode}")
    runner = SubprocessRunner()
    recycle_bin: RecycleBinSocket = LegacyRecycleBin(root, runner) if allow_deletion else NullRecycleBin()
    return SocketSet(
        entry=LegacyEntrySocket(root, runner),
        clipboard=LegacyClipboardSocket(root, runner),
        recycle_bin=recycle_bin,
        digest=LegacyDigestSocket(root, runner),
        menu=LegacyMenuSocket(runner),
        opener=LegacyFileOpenerSocket(runner),
        clock=SystemClock(),
    )


def _sealed_sockets() -> SocketSet:
    return SocketSet(
        entry=NullEntrySocket(),
        clipboard=NullClipboardSocket(),
        recycle_bin=NullRecycleBin(),
        digest=NullDigestSocket(),
        menu=NullMenuSocket(),
        opener=NullFileOpenerSocket(),
        clock=SystemClock(),
    )
