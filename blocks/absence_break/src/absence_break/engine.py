from __future__ import annotations

from datetime import datetime

from .models import AbsenceConfig, AbsenceState, BreakEvent, BreakEventKind, PresenceStatus


class AbsenceEngine:
    def __init__(self, config: AbsenceConfig | None = None, state: AbsenceState | None = None) -> None:
        self.config = config or AbsenceConfig()
        self.state = state or AbsenceState()

    def update(self, presence: PresenceStatus, now: datetime) -> tuple[BreakEvent, ...]:
        if presence is PresenceStatus.NEAR:
            return self._return(now)
        return self._absent(presence, now)

    def _absent(self, cause: PresenceStatus, now: datetime) -> tuple[BreakEvent, ...]:
        if self.state.pending_since is None:
            self.state = AbsenceState(now, cause, False)
            return ()
        if self.state.confirmed or now - self.state.pending_since < self.config.grace:
            return ()
        started = self.state.pending_since
        self.state = AbsenceState(started, self.state.cause, True)
        return (BreakEvent(BreakEventKind.STARTED, started, now),)

    def _return(self, now: datetime) -> tuple[BreakEvent, ...]:
        if self.state.pending_since is None:
            return ()
        was_confirmed = self.state.confirmed
        self.state = AbsenceState()
        if not was_confirmed:
            return ()
        return (BreakEvent(BreakEventKind.RETURNED, now, now),)
