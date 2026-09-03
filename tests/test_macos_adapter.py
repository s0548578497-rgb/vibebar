from __future__ import annotations

import json
from pathlib import Path
import unittest

from vibebar_macos.assembly import assemble_macos
from vibebar_macos.audio_cue import MacAudioCue
from vibebar_macos.bluetooth import NullBluetoothConnectionSocket, SystemProfilerBluetoothSocket
from vibebar_modular.contracts import CommandResult
from vibebar_modular.nulls import NullRecycleBin
from vibebar_modular.compositions import get_composition

ROOT = Path(__file__).resolve().parents[1]


class RecordingRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.calls: list[tuple[str, ...]] = []

    def run(self, arguments: tuple[str, ...] | list[str]) -> CommandResult:
        self.calls.append(tuple(arguments))
        return self.result


class MacAdapterTests(unittest.TestCase):
    def test_audio_uses_native_afplay_socket(self) -> None:
        runner = RecordingRunner(CommandResult(0))
        self.assertTrue(MacAudioCue(runner).play())
        self.assertEqual(runner.calls[0][0], "afplay")

    def test_bluetooth_parser_reads_named_connected_device(self) -> None:
        device = {"Headset": {"device_connected": "attrib_Yes"}}
        payload = {"SPBluetoothDataType": [{"devices_list": [device]}]}
        runner = RecordingRunner(CommandResult(0, json.dumps(payload)))
        self.assertTrue(SystemProfilerBluetoothSocket(runner, "headset").connected())

    def test_unknown_profiler_output_is_safe(self) -> None:
        runner = RecordingRunner(CommandResult(1, stderr="unavailable"))
        self.assertIsNone(SystemProfilerBluetoothSocket(runner, "headset").connected())

    def test_assembly_seals_optional_and_destructive_sockets(self) -> None:
        sockets = assemble_macos(ROOT)
        self.assertIsInstance(sockets.bluetooth, NullBluetoothConnectionSocket)
        self.assertIsInstance(sockets.core.recycle_bin, NullRecycleBin)

    def test_macos_and_windows_expose_the_same_actions(self) -> None:
        sockets = assemble_macos(ROOT)
        self.assertEqual(sockets.composition.actions, get_composition("windows").actions)


if __name__ == "__main__":
    unittest.main()
