"""Replaceable macOS global-hotkey adapter."""

from __future__ import annotations

from collections.abc import Callable


class MacGlobalHotkey:
    def __init__(self, callback: Callable[[], None], on_error: Callable[[str], None]) -> None:
        self.callback = callback
        self.on_error = on_error
        self.listener: object | None = None

    def start(self) -> None:
        if self.listener is not None:
            return
        try:
            from pynput import keyboard
            self.listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+<space>": self.callback})
            self.listener.start()
        except (ImportError, OSError, RuntimeError) as error:
            self.listener = None
            self.on_error(str(error))

    def close(self) -> None:
        listener = self.listener
        if listener is not None and hasattr(listener, "stop"):
            listener.stop()
        self.listener = None
