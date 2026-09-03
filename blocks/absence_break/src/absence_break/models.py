"""Value objects shared by absence detection and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class PresenceStatus(str, Enum):
    NEAR = "NEAR"
    FAR = "FAR"
    DISCONNECTED = "DISCONNECTED"


class BreakEventKind(str, Enum):
    STARTED = "STARTED"
    RETURNED = "RETURNED"


@dataclass(frozen=True, slots=True)
class BreakEvent:
    kind: BreakEventKind
    occurred_at: datetime
    detected_at: datetime


@dataclass(frozen=True, slots=True)
class AbsenceConfig:
    grace: timedelta = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class AbsenceState:
    pending_since: datetime | None = None
    cause: PresenceStatus | None = None
    confirmed: bool = False
