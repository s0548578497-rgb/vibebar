"""Event-driven cross-process journal refresh on Windows."""

from __future__ import annotations

import ctypes
import threading
from typing import Callable, Protocol


EVENT_NAME = "Local\\VibeBarJournalChanged"


class JournalChangeListener(Protocol):
    def start(self) -> None: ...
    def close(self) -> None: ...


class NullJournalChangeListener:
    def start(self) -> None:
        return None

    def close(self) -> None:
        return None


class WindowsJournalChangeListener:
    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.handle = ctypes.windll.kernel32.CreateEventW(None, False, False, EVENT_NAME)
        self.stopping = False
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.handle or self.thread is not None:
            return
        self.thread = threading.Thread(target=self._wait, name="journal-change-event", daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.stopping = True
        if self.handle:
            ctypes.windll.kernel32.SetEvent(self.handle)
        if self.thread is not None:
            self.thread.join(timeout=2)
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = 0

    def _wait(self) -> None:
        while not self.stopping:
            result = ctypes.windll.kernel32.WaitForSingleObject(self.handle, 0xFFFFFFFF)
            if result == 0 and not self.stopping:
                self.callback()
