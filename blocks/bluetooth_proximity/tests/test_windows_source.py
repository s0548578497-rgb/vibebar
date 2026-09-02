from __future__ import annotations

from pathlib import Path
import time
import unittest
from unittest.mock import patch

from bluetooth_proximity.windows_source import WindowsClassicRssiSource


class FakeProcess:
    def __init__(self) -> None:
        self.stdout = iter(("-51\n", "bad\n", "missing\n"))
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


class WindowsSourceTests(unittest.TestCase):
    @patch("bluetooth_proximity.windows_source.subprocess.Popen")
    def test_reader_output_becomes_typed_samples(self, popen: object) -> None:
        process = FakeProcess()
        popen.return_value = process
        source = WindowsClassicRssiSource(Path("reader.exe"), "headset", timeout=0.1)
        self.assertEqual(popen.call_args.args[0][-1], "relative")
        time.sleep(0.01)
        self.assertEqual(source.read().rssi, -51)
        self.assertIsNone(source.read().rssi)
        source.close()
        self.assertTrue(process.stopped)


if __name__ == "__main__":
    unittest.main()
