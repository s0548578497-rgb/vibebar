"""Download official openWakeWord models into local application data."""

from __future__ import annotations

import os
from pathlib import Path

import openwakeword
from faster_whisper import WhisperModel


def main() -> None:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    target = local / "VibeBar" / "models"
    target.mkdir(parents=True, exist_ok=True)
    openwakeword.utils.download_models(["hey_jarvis_v0.1"], str(target))
    WhisperModel("Systran/faster-whisper-small", device="cpu", compute_type="int8")


if __name__ == "__main__":
    main()
