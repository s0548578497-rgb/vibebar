from __future__ import annotations

from pathlib import Path
import time
import unittest
from unittest.mock import patch

from vibebar_macos.rssi_source import MacClassicRssiSource


class FakeProcess:
    def __init__(self, lines: tuple[str, ...]) -> None:
        self.stdout = iter(lines)
        self.stderr = iter(())
        self.stopped = False

    def poll(self) -> int | None:
        return 0 if self.stopped else None

    def terminate(self) -> None:
        self.stopped = True

    def wait(self, timeout: int) -> int:
        return 0

    def kill(self) -> None:
        self.stopped = True


class MacSourceTests(unittest.TestCase):
    @patch("bluetooth_proximity.process_source.subprocess.Popen")
    def test_native_lines_become_typed_samples(self, popen: object) -> None:
        process = FakeProcess(("-51\n", "unknown\n", "missing\n"))
        popen.return_value = process
        source = MacClassicRssiSource(Path("reader"), "headset", timeout=0.1)
        time.sleep(0.01)
        self.assertEqual(source.read().rssi, -51)
        self.assertIsNone(source.read().rssi)
        self.assertFalse(source.read().connected)
        source.close()


if __name__ == "__main__":
    unittest.main()
