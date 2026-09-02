"""Replaceable audible command acknowledgement."""

from __future__ import annotations

import io
import math
import struct
from typing import Protocol
import wave
import winsound


class AudioCue(Protocol):
    def play(self) -> None: ...


class NullAudioCue:
    def play(self) -> None:
        return None


class WindowsWaveCue:
    """Play a short WAV through the normal Windows waveform audio path."""

    def __init__(self, frequency: int = 880, duration_ms: int = 160, volume: float = 0.65) -> None:
        self.content = _tone(frequency, duration_ms, volume)

    def play(self) -> None:
        winsound.PlaySound(self.content, winsound.SND_MEMORY | winsound.SND_SYNC)


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
