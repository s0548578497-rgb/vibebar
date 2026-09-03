"""Replaceable audible command acknowledgement."""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
import struct
import wave
import winsound

from vibebar_modular.platform_contracts import AudioCue
from vibebar_modular.platform_nulls import NullAudioCue

class WindowsWaveCue:
    """Play a short WAV through the normal Windows waveform audio path."""

    def __init__(
        self, path: Path | None = None, frequency: int = 880, duration_ms: int = 160, volume: float = 0.65
    ) -> None:
        local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.path = path or local / "VibeBar" / "command-cue.wav"
        self.available = self._prepare(_tone(frequency, duration_ms, volume))

    def play(self) -> bool:
        if not self.available:
            return False
        try:
            winsound.PlaySound(
                str(self.path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            )
        except RuntimeError:
            return False
        return True

    def _prepare(self, content: bytes) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_bytes(content)
        except OSError:
            return False
        return True


def _tone(frequency: int, duration_ms: int, volume: float) -> bytes:
    sample_rate = 16_000
    sample_count = sample_rate * duration_ms // 1000
    peak = int(32_767 * max(0.0, min(volume, 1.0)))
    frames = bytearray()
    for index in range(sample_count):
        envelope = min(index / 160, (sample_count - index) / 160, 1.0)
        value = int(peak * envelope * math.sin(2 * math.pi * frequency * index / sample_rate))
        frames.extend(struct.pack("<h", value))
    output = io.BytesIO()
    with wave.open(output, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(sample_rate)
        sound.writeframes(frames)
    return output.getvalue()
