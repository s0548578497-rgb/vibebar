"""macOS Bluetooth-disconnect service over the shared absence engine."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import threading

from absence_break.clock import SystemClock
from absence_break.coordinator import AbsenceCoordinator
from absence_break.engine import AbsenceEngine
from absence_break.journal_writer import MarkdownJournalBreakWriter
from absence_break.models import PresenceStatus
from absence_break.state_store import JsonStateStore
from bluetooth_proximity.config_store import JsonConfigStore
from bluetooth_proximity.engine import ProximityEngine
from bluetooth_proximity.models import ProximityState
from bluetooth_proximity.resilience import RestartingSignalSource, SourceHealthSink
from vibebar_voice.diagnostics import JsonLineDiagnosticLog

from .rssi_source import MacClassicRssiSource


class DiagnosticHealthSink(SourceHealthSink):
    def __init__(self, diagnostics: JsonLineDiagnosticLog) -> None:
        self.diagnostics = diagnostics

    def report(self, event: str) -> None:
        self.diagnostics.event(event.lower())


def main() -> None:
    device = os.environ.get("VIBEBAR_BLUETOOTH_DEVICE", "").strip()
    if not device:
        return
    root = Path(__file__).resolve().parents[1]
    runtime = root / "macos" / "runtime"
    clock = SystemClock()
    diagnostics = JsonLineDiagnosticLog(runtime / "absence.jsonl", clock)
    store = JsonStateStore(runtime / "absence-state.json")
    coordinator = AbsenceCoordinator(
        AbsenceEngine(state=store.load()),
        MarkdownJournalBreakWriter(Path.home() / "vibebar-journal.md"),
        store,
    )
    reader = root / "macos" / "native" / "ClassicRssiReader"
    source = RestartingSignalSource(
        lambda: MacClassicRssiSource(reader, device),
        health=DiagnosticHealthSink(diagnostics),
    )
    engine = ProximityEngine(JsonConfigStore(root / "resources" / "proximity" / "macos_default.json").load())
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda _number, _frame: stopped.set())
    signal.signal(signal.SIGINT, lambda _number, _frame: stopped.set())
    diagnostics.event("absence_monitor_started", device_configured=True)
    while not stopped.is_set():
        proximity = engine.update(source.read())
        presence = _presence(proximity)
        if presence is not None:
            coordinator.update(presence, clock.now())
        else:
            diagnostics.event("bluetooth_unknown")
        stopped.wait(5)
    source.close()


def _presence(state: ProximityState) -> PresenceStatus | None:
    mapping = {
        ProximityState.NEAR: PresenceStatus.NEAR,
        ProximityState.FAR: PresenceStatus.FAR,
        ProximityState.DISCONNECTED: PresenceStatus.DISCONNECTED,
    }
    return mapping.get(state)


if __name__ == "__main__":
    main()
