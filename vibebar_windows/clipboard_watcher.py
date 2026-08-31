"""Opt-in Windows clipboard watcher with no disk logging of clipboard data."""

from __future__ import annotations

import hashlib
import tkinter as tk
from typing import Callable

from vibebar_modular.contracts import ClipboardSocket


class ClipboardWatcher:
    def __init__(
        self,
        root: tk.Tk,
        socket: ClipboardSocket,
        on_saved: Callable[[], None],
        interval_ms: int = 1200,
    ) -> None:
        self.root = root
        self.socket = socket
        self.on_saved = on_saved
        self.interval_ms = interval_ms
        self.enabled = False
        self.last_hash = ""

    def start(self) -> None:
        self.enabled = True
        self.last_hash = self._current_hash()
        self._schedule()

    def stop(self) -> None:
        self.enabled = False

    def toggle(self) -> bool:
        if self.enabled:
            self.stop()
        else:
            self.start()
        return self.enabled

    def mark_current_seen(self) -> None:
        self.last_hash = self._current_hash()

    def _schedule(self) -> None:
        self.root.after(self.interval_ms, self._poll)

    def _poll(self) -> None:
        if not self.enabled:
            return
        current = self._current_hash()
        if current and current != self.last_hash:
            self.last_hash = current
            result = self.socket.add_current()
            if result.succeeded:
                self.on_saved()
        self._schedule()

    def _current_hash(self) -> str:
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return ""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
