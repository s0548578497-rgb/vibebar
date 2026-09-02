from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import SignalSource
from .engine import ProximityEngine
from .models import ProximityState


@dataclass(slots=True)
class ProximityMonitor:
    source: SignalSource
    engine: ProximityEngine
    on_change: Callable[[ProximityState], None]

    def poll(self) -> ProximityState:
        previous = self.engine.state
        current = self.engine.update(self.source.read())
        if current != previous:
            self.on_change(current)
        return current
