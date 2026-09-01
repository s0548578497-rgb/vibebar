"""Transcription contract and safe sealed implementation."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class AudioTranscriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...
    def close(self) -> None: ...


class NullAudioTranscriber:
    def transcribe(self, audio: np.ndarray) -> str:
        return ""

    def close(self) -> None:
        return None
