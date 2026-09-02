from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from absence_break.contracts import NullBreakWriter, NullStateStore
from absence_break.coordinator import AbsenceCoordinator
from absence_break.engine import AbsenceEngine
from absence_break.journal_writer import MarkdownJournalBreakWriter
from absence_break.models import AbsenceState, BreakEvent, BreakEventKind, PresenceStatus
from absence_break.state_store import JsonStateStore


START = datetime(2030, 1, 2, 10, 0)


class RecordingWriter:
    def __init__(self) -> None:
        self.events: list[BreakEvent] = []

    def write(self, event: BreakEvent) -> None:
        self.events.append(event)


class AbsenceTests(unittest.TestCase):
    def test_short_exit_is_cancelled(self) -> None:
        engine = AbsenceEngine()
        self.assertEqual(engine.update(PresenceStatus.FAR, START), ())
        self.assertEqual(engine.update(PresenceStatus.NEAR, START + timedelta(minutes=4)), ())

    def test_five_minutes_creates_retroactive_break(self) -> None:
        engine = AbsenceEngine()
        engine.update(PresenceStatus.FAR, START)
        event = engine.update(PresenceStatus.FAR, START + timedelta(minutes=5))[0]
        self.assertEqual(event.kind, BreakEventKind.STARTED)
        self.assertEqual(event.occurred_at, START)

    def test_disconnect_uses_the_same_grace_period(self) -> None:
        engine = AbsenceEngine()
        engine.update(PresenceStatus.DISCONNECTED, START)
        self.assertEqual(engine.update(PresenceStatus.DISCONNECTED, START + timedelta(minutes=4)), ())
        self.assertEqual(engine.update(PresenceStatus.DISCONNECTED, START + timedelta(minutes=5))[0].occurred_at, START)

    def test_return_after_confirmed_break_emits_return(self) -> None:
        engine = AbsenceEngine(state=AbsenceState(START, PresenceStatus.FAR, True))
        event = engine.update(PresenceStatus.NEAR, START + timedelta(minutes=8))[0]
        self.assertEqual(event.kind, BreakEventKind.RETURNED)

    def test_state_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonStateStore(Path(directory) / "state.json")
            state = AbsenceState(START, PresenceStatus.FAR, False)
            store.save(state)
            self.assertEqual(store.load(), state)

    def test_null_boundaries_are_safe(self) -> None:
        engine = AbsenceEngine()
        coordinator = AbsenceCoordinator(engine, NullBreakWriter(), NullStateStore())
        coordinator.update(PresenceStatus.FAR, START)

    def test_writer_is_retroactive_idempotent_and_resumes_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.md"
            journal.write_text("## 2030-01-02\n- 09:00 · כתיבה\n", encoding="utf-8")
            writer = MarkdownJournalBreakWriter(journal)
            started = BreakEvent(BreakEventKind.STARTED, START, START + timedelta(minutes=5))
            returned = BreakEvent(BreakEventKind.RETURNED, START + timedelta(minutes=8), START + timedelta(minutes=8))
            writer.write(started); writer.write(started); writer.write(returned)
            content = journal.read_text(encoding="utf-8")
            self.assertEqual(content.count("הפסקה אוטומטית"), 1)
            self.assertIn("10:08 · כתיבה", content)


if __name__ == "__main__":
    unittest.main()
