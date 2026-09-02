from __future__ import annotations

from collections import deque
from statistics import median

from .models import ProximityConfig, ProximityState, SignalSample


class ProximityEngine:
    def __init__(self, config: ProximityConfig | None = None) -> None:
        self.config = config or ProximityConfig()
        self.config.validate()
        self.values: deque[int] = deque(maxlen=self.config.window_size)
        self.state = ProximityState.UNKNOWN
        self.candidate = ProximityState.UNKNOWN
        self.candidate_count = 0
        self.missing_count = 0

    def update(self, sample: SignalSample) -> ProximityState:
        if sample.rssi is None:
            return self._missing()
        self.missing_count = 0
        self.values.append(sample.rssi)
        proposed = self._propose(int(median(self.values)))
        self._confirm(proposed)
        return self.state

    def _missing(self) -> ProximityState:
        self.missing_count += 1
        if self.missing_count >= self.config.missing_limit:
            self.state = ProximityState.UNKNOWN
            self._reset_candidate()
        return self.state

    def _propose(self, filtered: int) -> ProximityState:
        if filtered <= self.config.far_threshold:
            return ProximityState.FAR
        if filtered >= self.config.near_threshold:
            return ProximityState.NEAR
        return self.state

    def _confirm(self, proposed: ProximityState) -> None:
        if proposed in (self.state, ProximityState.UNKNOWN):
            self._reset_candidate()
            return
        if proposed != self.candidate:
            self.candidate = proposed
            self.candidate_count = 0
        self.candidate_count += 1
        if self.candidate_count >= self.config.confirmations:
            self.state = proposed
            self._reset_candidate()

    def _reset_candidate(self) -> None:
        self.candidate = ProximityState.UNKNOWN
        self.candidate_count = 0
