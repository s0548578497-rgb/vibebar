"""Replaceable global-hotkey boundary for Windows."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import threading
from typing import Callable

from vibebar_modular.platform_contracts import GlobalHotkey
from vibebar_modular.platform_nulls import NullGlobalHotkey

class WindowsGlobalHotkey:
    HOTKEY_ID = 0x5642
    WM_HOTKEY = 0x0312
    WM_QUIT = 0x0012
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_NOREPEAT = 0x4000
    VK_SPACE = 0x20

    def __init__(self, callback: Callable[[], None], on_error: Callable[[str], None]) -> None:
        self.callback = callback
        self.on_error = on_error
        self.thread: threading.Thread | None = None
        self.thread_id = 0
        self.ready = threading.Event()

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        self.ready.clear()
        self.thread = threading.Thread(target=self._run, name="vibebar-hotkey", daemon=True)
        self.thread.start()
        self.ready.wait(timeout=1)

    def _run(self) -> None:
        user32 = ctypes.windll.user32
        self.thread_id = int(ctypes.windll.kernel32.GetCurrentThreadId())
        modifiers = self.MOD_CONTROL | self.MOD_ALT | self.MOD_NOREPEAT
        registered = bool(user32.RegisterHotKey(None, self.HOTKEY_ID, modifiers, self.VK_SPACE))
        self.ready.set()
        if not registered:
            self.on_error("Ctrl+Alt+Space is already in use")
            return
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == self.WM_HOTKEY and message.wParam == self.HOTKEY_ID:
                    self.callback()
        finally:
            user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def close(self) -> None:
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, self.WM_QUIT, 0, 0)
        if self.thread is not None:
            self.thread.join(timeout=1)
        self.thread = None
        self.thread_id = 0
