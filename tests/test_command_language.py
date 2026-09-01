from pathlib import Path
import unittest

from vibebar_modular.contracts import CommandResult
from vibebar_windows.command_language import CommandVocabulary, LocalizedEntrySocket


class RecordingEntry:
    def __init__(self) -> None:
        self.values: list[str] = []

    def submit(self, text: str) -> CommandResult:
        self.values.append(text)
        return CommandResult(0)


class CommandLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.inner = RecordingEntry()
        words = CommandVocabulary.load(root / "windows" / "command_words.json")
        self.socket = LocalizedEntrySocket(self.inner, words)

    def test_hebrew_idea(self) -> None:
        self.socket.submit("רעיון לכתוב ספר")
        self.assertEqual(self.inner.values[-1], "идея לכתוב ספר")

    def test_hebrew_multiword_reminder(self) -> None:
        self.socket.submit("לא לשכוח להתקשר ליוסי")
        self.assertEqual(self.inner.values[-1], "не забыть להתקשר ליוסי")

    def test_hebrew_pause(self) -> None:
        self.socket.submit("הפסקה בבקשה")
        self.assertEqual(self.inner.values[-1], "перерыв")

    def test_regular_task_is_unchanged(self) -> None:
        self.socket.submit("עובד על המצגת")
        self.assertEqual(self.inner.values[-1], "עובד על המצגת")


if __name__ == "__main__":
    unittest.main()
