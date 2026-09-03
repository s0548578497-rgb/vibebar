from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from vibebar_modular.achievements import MarkdownAchievementSocket, PendingAchievementCapture


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 3, 14, 30)


class AchievementTests(unittest.TestCase):
    def test_note_is_separate_and_does_not_become_a_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.md"
            socket = MarkdownAchievementSocket(journal, FixedClock())
            self.assertTrue(socket.add("כתבתי את הפרק הראשון").succeeded)
            self.assertEqual(socket.load_today()[0].text, "כתבתי את הפרק הראשון")
            self.assertIn("✅ כתבתי את הפרק הראשון", journal.read_text(encoding="utf-8"))

    def test_capture_routes_only_the_next_transcription(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            socket = MarkdownAchievementSocket(Path(directory) / "journal.md", FixedClock())
            capture = PendingAchievementCapture(socket, monotonic=lambda: 10.0)
            capture.arm()
            self.assertTrue(capture.submit_if_armed("סיימתי").succeeded)
            self.assertIsNone(capture.submit_if_armed("משימה חדשה"))
