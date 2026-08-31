from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from vibebar_modular.compositions import Action, get_composition
from vibebar_windows.paths import WindowsPaths
from vibebar_windows.runner import WindowsBashRunner, _to_git_path
from vibebar_windows.assembly import assemble_windows


ROOT = Path(__file__).resolve().parents[1]


class WindowsPathTests(unittest.TestCase):
    def test_absolute_windows_path_becomes_git_path(self) -> None:
        self.assertEqual(_to_git_path("C:/work/file.txt"), "/c/work/file.txt")

    def test_plain_argument_is_unchanged(self) -> None:
        self.assertEqual(_to_git_path("original text"), "original text")

    def test_windows_composition_matches_desktop_controls(self) -> None:
        actions = get_composition("windows").actions
        self.assertIn(Action.ADD_ENTRY, actions)
        self.assertIn(Action.DELETE_CLIPBOARD, actions)
        self.assertIn(Action.WEEKLY_DIGEST, actions)
        self.assertIn(Action.OPEN_JOURNAL, actions)


class WindowsRunnerTests(unittest.TestCase):
    @patch("vibebar_windows.runner.subprocess.run")
    def test_runner_injects_python_utf8_and_shims(self, run: object) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""
        paths = WindowsPaths(Path("C:/repo"), Path("C:/Git/bin/bash.exe"), Path(sys.executable), Path("C:/repo/windows/bin"))
        WindowsBashRunner(paths).run(("C:/repo/bin/vibebar-add.sh", "text"))
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["PYTHONUTF8"], "1")
        self.assertIn("windows\\bin", environment["PATH"])

    @unittest.skipUnless(sys.platform == "win32", "Windows integration test")
    def test_original_entry_script_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            journal = Path(directory) / "journal.md"
            sockets = assemble_windows(ROOT, {"VIBEBAR_FILE": str(journal)})
            result = sockets.entry.submit("adapter integration test")
            self.assertTrue(result.succeeded, result.stderr)
            self.assertIn("adapter integration test", journal.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
