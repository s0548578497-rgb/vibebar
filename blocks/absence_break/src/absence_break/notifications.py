from __future__ import annotations

import ctypes
from typing import Protocol


EVENT_NAME = "Local\\VibeBarJournalChanged"


class ChangeNotifier(Protocol):
    def notify(self) -> None: ...


class NullChangeNotifier:
    def notify(self) -> None:
        return None


class WindowsNamedEventNotifier:
    def notify(self) -> None:
        handle = ctypes.windll.kernel32.OpenEventW(0x0002, False, EVENT_NAME)
        if not handle:
            return
        ctypes.windll.kernel32.SetEvent(handle)
        ctypes.windll.kernel32.CloseHandle(handle)
