"""Headless macOS voice service using the shared local pipeline."""

from __future__ import annotations

from pathlib import Path
import signal
import threading

from vibebar_voice.controller import VoiceController
from vibebar_voice.diagnostics import JsonLineDiagnosticLog

from .assembly import assemble_macos
from .hotkey import MacGlobalHotkey
from .voice_state import VoiceState


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sockets = assemble_macos(root)
    diagnostics = JsonLineDiagnosticLog(root / "macos" / "diagnostics.jsonl", sockets.core.clock)
    stopped = threading.Event()
    enabled = VoiceState(root / "macos" / "voice.json").enabled()

    def status(value: str) -> None:
        diagnostics.event("voice_status", value=value)

    def submit(text: str) -> None:
        result = sockets.core.entry.submit(text)
        diagnostics.event("entry_submitted", succeeded=result.succeeded)
        if result.succeeded:
            sockets.core.menu.refresh()

    voice = VoiceController(
        submit,
        status,
        sockets.transcriber_factory(),
        model_dir=sockets.model_dir,
        wakeword=sockets.wakeword,
        cue=sockets.audio_cue,
        diagnostics=diagnostics,
    )
    hotkey = MacGlobalHotkey(voice.request_command, status)
    signal.signal(signal.SIGTERM, lambda _number, _frame: stopped.set())
    signal.signal(signal.SIGINT, lambda _number, _frame: stopped.set())
    if enabled:
        hotkey.start()
        voice.start()
    stopped.wait()
    if enabled:
        hotkey.close()
        voice.close()


if __name__ == "__main__":
    main()
