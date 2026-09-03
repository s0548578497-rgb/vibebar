from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

from vibebar_modular.assembly import assemble
from vibebar_modular.compositions import Action, get_composition
from vibebar_modular.contracts import CommandResult
from vibebar_modular.legacy import LegacyDigestSocket, LegacyEntrySocket
from vibebar_modular.nulls import (
    NullClipboardSocket,
    NullDigestSocket,
    NullEntrySocket,
    NullFileOpenerSocket,
    NullMenuSocket,
    NullRecycleBin,
)
from vibebar_modular.sockets import build_sockets


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, arguments: tuple[str, ...] | list[str]) -> CommandResult:
        self.calls.append(tuple(arguments))
        return CommandResult(0, "legacy-output")


class LegacyAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("/repository")
        self.runner = RecordingRunner()

    def test_entry_adapter_delegates_without_transforming_text(self) -> None:
        socket = LegacyEntrySocket(self.root, self.runner)
        result = socket.submit("original text")
        self.assertTrue(result.succeeded)
        self.assertEqual(
            self.runner.calls,
            [(str(self.root / "bin" / "vibebar-add.sh"), "original text")],
        )

    def test_digest_adapter_preserves_legacy_arguments(self) -> None:
        socket = LegacyDigestSocket(self.root, self.runner)
        socket.build_day(rebuild=True)
        socket.build_week(date(2030, 1, 2))
        self.assertEqual(self.runner.calls[0][-1], "--rebuild")
        self.assertEqual(self.runner.calls[1][-1], "2030-01-02")


class SafeDirectionTests(unittest.TestCase):
    def test_null_entry_reports_failure_instead_of_losing_input_silently(self) -> None:
        result = NullEntrySocket().submit("unsaved text")
        self.assertFalse(result.succeeded)

    def test_null_recycle_bin_never_invokes_external_code(self) -> None:
        recycle_bin = NullRecycleBin()
        self.assertFalse(recycle_bin.delete_clipboard_item(2).succeeded)
        self.assertFalse(recycle_bin.clear_clipboard().succeeded)

    def test_identity_mode_seals_deletion_by_default(self) -> None:
        sockets = build_sockets(Path("/repository"))
        self.assertIsInstance(sockets.recycle_bin, NullRecycleBin)

    def test_every_disconnected_command_reports_failure(self) -> None:
        results = (
            NullClipboardSocket().add_current(),
            NullClipboardSocket().copy(1),
            NullClipboardSocket().show(1),
            NullDigestSocket().build_day(),
            NullDigestSocket().build_week(),
            NullDigestSocket().publish_day(),
            NullMenuSocket().refresh(),
            NullFileOpenerSocket().open(Path("journal.md")),
        )
        self.assertTrue(all(not result.succeeded for result in results))


class CompositionTests(unittest.TestCase):
    def test_pilot_exposes_only_connected_actions(self) -> None:
        pilot = get_composition("pilot")
        self.assertTrue(pilot.contains(Action.ADD_ENTRY))
        self.assertFalse(pilot.contains(Action.DELETE_CLIPBOARD))

    def test_full_contains_every_declared_action(self) -> None:
        self.assertEqual(get_composition("full").actions, frozenset(Action))

    def test_assembly_connects_deletion_only_when_control_is_visible(self) -> None:
        pilot = assemble(Path("/repository"), "pilot")
        full = assemble(Path("/repository"), "full")
        self.assertIsInstance(pilot.sockets.recycle_bin, NullRecycleBin)
        self.assertNotIsInstance(full.sockets.recycle_bin, NullRecycleBin)
        self.assertNotIn(Action.DELETE_CLIPBOARD, pilot.visible_actions)
        self.assertIn(Action.DELETE_CLIPBOARD, full.visible_actions)


if __name__ == "__main__":
    unittest.main()
