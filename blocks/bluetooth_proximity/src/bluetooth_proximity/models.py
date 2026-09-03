"""Typed samples, states and thresholds for proximity detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProximityState(str, Enum):
    UNKNOWN = "UNKNOWN"
    NEAR = "NEAR"
    FAR = "FAR"
    DISCONNECTED = "DISCONNECTED"


@dataclass(frozen=True, slots=True)
class SignalSample:
    rssi: int | None
    connected: bool | None = None


@dataclass(frozen=True, slots=True)
class ProximityConfig:
    near_threshold: int = -67
    far_threshold: int = -78
    window_size: int = 5
    confirmations: int = 3
    missing_limit: int = 5

    def validate(self) -> None:
        if self.near_threshold <= self.far_threshold:
            raise ValueError("near_threshold must be stronger than far_threshold")
        if min(self.window_size, self.confirmations, self.missing_limit) < 1:
            raise ValueError("window and counters must be positive")
