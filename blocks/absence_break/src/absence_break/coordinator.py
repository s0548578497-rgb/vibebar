from __future__ import annotations

from datetime import datetime

from .contracts import BreakWriter, StateStore
from .engine import AbsenceEngine
from .models import PresenceStatus


class AbsenceCoordinator:
    def __init__(self, engine: AbsenceEngine, writer: BreakWriter, store: StateStore) -> None:
        self.engine = engine
        self.writer = writer
        self.store = store

    def update(self, presence: PresenceStatus, now: datetime) -> None:
        events = self.engine.update(presence, now)
        for event in events:
            self.writer.write(event)
        self.store.save(self.engine.state)
