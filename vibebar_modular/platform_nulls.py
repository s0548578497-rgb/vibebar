"""Safe sealed plates for optional operating-system services."""

from __future__ import annotations


class NullAudioCue:
    def play(self) -> bool:
        return False


class NullGlobalHotkey:
    def start(self) -> None:
        return None

    def close(self) -> None:
        return None


class NullJournalChangeListener:
    def start(self) -> None:
        return None

    def close(self) -> None:
        return None
