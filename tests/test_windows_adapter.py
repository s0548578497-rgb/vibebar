from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from vibebar_modular.compositions import Action, get_composition
from vibebar_windows.paths import WindowsPaths
from vibebar_windows.runner import WindowsBashRunner, _to_git_path
from vibebar_windows.assembly import assemble_menu_view, assemble_windows, default_environment
from vibebar_windows.digests import WindowsDigestSocket
from vibebar_modular.clock import FixedClock
from vibebar_modular.contracts import CommandResult
from vibebar_modular.legacy import LegacyDigestSocket


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
        self.assertNotEqual(run.call_args.kwargs["creationflags"], 0)

    @unittest.skipUnless(sys.platform == "win32", "Windows integration test")
    def test_original_entry_script_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            journal = Path(directory) / "journal.md"
            sockets = assemble_windows(ROOT, {"VIBEBAR_FILE": str(journal)})
            result = sockets.entry.submit("adapter integration test")
            self.assertTrue(result.succeeded, result.stderr)
            self.assertIn("adapter integration test", journal.read_text(encoding="utf-8"))

    @unittest.skipUnless(sys.platform == "win32", "Windows integration test")
    def test_live_menu_renderer_uses_injected_windows_python(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            journal = Path(directory) / "journal.md"
            journal.write_text(f"## {date.today():%Y-%m-%d}\n- 12:00 · visible entry\n", encoding="utf-8")
            environment = default_environment(ROOT)
            environment["VIBEBAR_FILE"] = str(journal)
            view = assemble_menu_view(
                ROOT, environment, FixedClock(datetime(2030, 1, 2, 12, 1)),
            ).load()
            self.assertTrue(any(item.text == "visible entry" for item in view.tasks))


class WindowsDigestTests(unittest.TestCase):
    def test_weekly_button_creates_local_report_without_obsidian(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            folder = Path(directory)
            runner = RecordingDigestRunner("weekly report")
            legacy = LegacyDigestSocket(ROOT, runner)
            socket = WindowsDigestSocket(
                ROOT,
                folder / "digests",
                folder / "journal.md",
                runner,
                legacy,
                FixedClock(datetime(2030, 1, 2, 12, 0)),
            )
            result = socket.build_week()
            report = folder / "digests" / "week-2030-01-02.md"
            self.assertTrue(result.succeeded)
            self.assertEqual(Path(result.stdout), report)
            self.assertEqual(report.read_text(encoding="utf-8"), "weekly report")
            self.assertTrue(runner.calls[0][0].endswith("vibebar-week.py"))

    def test_publish_remains_a_separate_legacy_action(self) -> None:
        runner = RecordingDigestRunner("")
        legacy = LegacyDigestSocket(ROOT, runner)
        socket = WindowsDigestSocket(
            ROOT, ROOT / "digests", ROOT / "journal.md", runner, legacy,
            FixedClock(datetime(2030, 1, 2, 12, 0)),
        )
        socket.publish_day(date(2030, 1, 1))
        self.assertTrue(runner.calls[0][0].endswith("vibebar-push-vault.sh"))


class RecordingDigestRunner:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[str, ...]] = []

    def run(self, arguments: tuple[str, ...] | list[str]) -> CommandResult:
        self.calls.append(tuple(arguments))
        return CommandResult(0, self.output)


if __name__ == "__main__":
    unittest.main()
