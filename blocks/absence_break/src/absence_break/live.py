from __future__ import annotations

import json
import os
from pathlib import Path

from bluetooth_proximity.config_store import JsonConfigStore
from bluetooth_proximity.engine import ProximityEngine
from bluetooth_proximity.models import ProximityState
from bluetooth_proximity.windows_source import WindowsClassicRssiSource

from .clock import SystemClock
from .coordinator import AbsenceCoordinator
from .engine import AbsenceEngine
from .journal_writer import MarkdownJournalBreakWriter
from .models import BreakEvent, PresenceStatus
from .state_store import JsonStateStore


class LoggedBreakWriter:
    def __init__(self, inner: MarkdownJournalBreakWriter, log: Path) -> None:
        self.inner = inner
        self.log = log

    def write(self, event: BreakEvent) -> None:
        self.inner.write(event)
        _log(self.log, event.kind.value, event.occurred_at.isoformat())


def main() -> None:
    repository = Path(__file__).resolve().parents[4]
    proximity = repository / "blocks" / "bluetooth_proximity"
    runtime = repository / "blocks" / "absence_break" / "runtime"
    store = JsonStateStore(runtime / "state.json")
    absence = AbsenceEngine(state=store.load())
    writer = LoggedBreakWriter(MarkdownJournalBreakWriter(Path.home() / "vibebar-journal.md"), runtime / "events.jsonl")
    coordinator = AbsenceCoordinator(absence, writer, store)
    engine = ProximityEngine(JsonConfigStore(proximity / "profiles" / "mediatek_relative.json").load())
    source = WindowsClassicRssiSource(proximity / "native" / "ClassicRssiReader.exe", "JBL TUNE125BT")
    clock = SystemClock()
    log = runtime / "events.jsonl"
    _log(log, "MONITOR_STARTED", clock.now().isoformat(), pid=os.getpid())
    previous = ProximityState.UNKNOWN
    try:
        while True:
            state = engine.update(source.read())
            if state is not previous:
                _log(log, "PROXIMITY", clock.now().isoformat(), state=state.value)
                previous = state
            presence = _presence(state)
            if presence is not None:
                coordinator.update(presence, clock.now())
    except KeyboardInterrupt:
        return
    finally:
        source.close()


def _presence(state: ProximityState) -> PresenceStatus | None:
    mapping = {
        ProximityState.NEAR: PresenceStatus.NEAR,
        ProximityState.FAR: PresenceStatus.FAR,
        ProximityState.DISCONNECTED: PresenceStatus.DISCONNECTED,
    }
    return mapping.get(state)


def _log(path: Path, event: str, at: str, **fields: str | int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"event": event, "at": at, **fields}, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
