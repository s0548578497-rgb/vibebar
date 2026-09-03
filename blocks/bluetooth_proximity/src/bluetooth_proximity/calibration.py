"""Derive conservative near/far thresholds from captured RSSI samples."""

from __future__ import annotations

from statistics import median

from .models import ProximityConfig


def calibrate(near_samples: list[int], far_samples: list[int]) -> ProximityConfig:
    if len(near_samples) < 3 or len(far_samples) < 3:
        raise ValueError("at least three samples are required for each zone")
    near = int(median(near_samples))
    far = int(median(far_samples))
    if near <= far:
        raise ValueError("near samples must be stronger than far samples")
    gap = near - far
    return ProximityConfig(near_threshold=far + gap * 2 // 3, far_threshold=far + gap // 3)
