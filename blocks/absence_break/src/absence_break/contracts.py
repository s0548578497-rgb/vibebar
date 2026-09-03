"""Persistence and journal contracts for the absence-break engine."""

from __future__ import annotations

from typing import Protocol

from .models import AbsenceState, BreakEvent


class BreakWriter(Protocol):
    def write(self, event: BreakEvent) -> None: ...


class StateStore(Protocol):
    def load(self) -> AbsenceState: ...
    def save(self, state: AbsenceState) -> None: ...


class NullBreakWriter:
    def write(self, event: BreakEvent) -> None:
        return None


class NullStateStore:
    def load(self) -> AbsenceState:
        return AbsenceState()

    def save(self, state: AbsenceState) -> None:
        return None
