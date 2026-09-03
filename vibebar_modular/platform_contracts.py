"""Contracts shared by operating-system adapters."""

from __future__ import annotations

from typing import Protocol


class AudioCue(Protocol):
    def play(self) -> bool: ...


class GlobalHotkey(Protocol):
    def start(self) -> None: ...
    def close(self) -> None: ...


class JournalChangeListener(Protocol):
    def start(self) -> None: ...
    def close(self) -> None: ...
