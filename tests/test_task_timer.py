from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from vibebar_windows.task_timer import JournalTaskTimerSocket, NullTaskTimerSocket


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 1, 14, 45, 30)


class TaskTimerTests(unittest.TestCase):
    def test_timer_uses_saved_start_and_ignores_ideas(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.md"
            journal.write_text(
                "## 2026-09-01\n- 14:30 · כתיבה\n- 14:40 · 💡 רעיון\n",
                encoding="utf-8",
            )
            state = JournalTaskTimerSocket(journal, FixedClock()).load()
            self.assertEqual(state.display(FixedClock().now()), "כתיבה · 15m")

    def test_pause_has_no_running_timer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.md"
            journal.write_text("## 2026-09-01\n- 14:30 · ⏸ הפסקה\n", encoding="utf-8")
            self.assertEqual(JournalTaskTimerSocket(journal, FixedClock()).load().display(FixedClock().now()), "—")

    def test_null_timer_is_sealed(self) -> None:
        self.assertEqual(NullTaskTimerSocket().load().display(FixedClock().now()), "—")


if __name__ == "__main__":
    unittest.main()
