from pathlib import Path
import tempfile
import unittest

from vibebar_modular.contracts import CommandResult
from vibebar_modular.command_language import CommandVocabulary, LocalizedEntrySocket
from vibebar_windows.custom_commands import CustomCommandStore, NullCustomCommandStore


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
        words = CommandVocabulary.load(root / "resources" / "command_words.json")
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

    def test_custom_task_keeps_its_phrase(self) -> None:
        words = self.socket.vocabulary.merged({"task": ("פגישת צוות",)})
        socket = LocalizedEntrySocket(self.inner, words)
        socket.submit("פגישת צוות")
        self.assertEqual(self.inner.values[-1], "פגישת צוות")


class CustomCommandStoreTests(unittest.TestCase):
    def test_null_store_is_sealed(self) -> None:
        store = NullCustomCommandStore()
        store.add("הפסקת אוכל", "pause")
        store.delete("הפסקת אוכל")
        self.assertEqual(store.load(), ())

    def test_commands_are_persisted_replaced_and_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CustomCommandStore(Path(directory) / "commands.json")
            store.add("הפסקת אוכל", "pause")
            self.assertEqual(store.load()[0].kind, "pause")
            store.add("הפסקת אוכל", "task")
            self.assertEqual(store.load()[0].kind, "task")
            store.delete("הפסקת אוכל")
            self.assertEqual(store.load(), ())


if __name__ == "__main__":
    unittest.main()
