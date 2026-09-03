"""Replaceable speech-boundary detection adapted from voice_agent LiveCutter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class BoundaryDecision:
    speech_seen: bool
    finished: bool
    level: float
    threshold: float


class SpeechBoundary(Protocol):
    @property
    def calibration_blocks(self) -> int: ...

    def calibrate(self, frame: np.ndarray) -> None: ...

    def observe(self, frame: np.ndarray) -> BoundaryDecision: ...


@dataclass(frozen=True, slots=True)
class AdaptiveBoundarySettings:
    sample_rate: int = 16_000
    block_size: int = 1_280
    end_silence_seconds: float = 1.50
    calibration_seconds: float = 0.50
    noise_multiplier: float = 1.60
    absolute_floor: float = 0.004
    floor_attack: float = 0.05


class AdaptiveSpeechBoundary:
    """Track ambient noise and end only after post-speech quiet."""

    def __init__(self, settings: AdaptiveBoundarySettings | None = None) -> None:
        self.settings = settings or AdaptiveBoundarySettings()
        blocks_per_second = self.settings.sample_rate / self.settings.block_size
        self._calibration_blocks = max(1, round(self.settings.calibration_seconds * blocks_per_second))
        self.end_blocks = max(1, round(self.settings.end_silence_seconds * blocks_per_second))
        self.calibration: list[float] = []
        self.floor = self.settings.absolute_floor
        self.speech_seen = False
        self.quiet_blocks = 0

    @property
    def calibration_blocks(self) -> int:
        return self._calibration_blocks

    def calibrate(self, frame: np.ndarray) -> None:
        self.calibration.append(self._level(frame))
        self.floor = max(float(np.median(self.calibration)), self.settings.absolute_floor)

    def observe(self, frame: np.ndarray) -> BoundaryDecision:
        level = self._level(frame)
        threshold = max(self.floor * self.settings.noise_multiplier, self.settings.absolute_floor)
        voiced = level > threshold
        if voiced:
            self.speech_seen = True
            self.quiet_blocks = 0
        elif self.speech_seen:
            self.quiet_blocks += 1
        else:
            attack = self.settings.floor_attack
            self.floor = (1.0 - attack) * self.floor + attack * level
        return BoundaryDecision(self.speech_seen, self.speech_seen and self.quiet_blocks >= self.end_blocks,
                                level * 32_768.0, threshold * 32_768.0)

    @staticmethod
    def _level(frame: np.ndarray) -> float:
        normalized = frame.astype(np.float64) / 32_768.0
        return float(np.sqrt(np.mean(normalized ** 2)))
