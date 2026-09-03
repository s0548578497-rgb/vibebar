from __future__ import annotations

import unittest

from bluetooth_proximity.models import SignalSample
from bluetooth_proximity.resilience import RestartingSignalSource


class FakeSource:
    def __init__(self, samples: list[SignalSample]) -> None:
        self.samples = iter(samples)
        self.closed = False

    def read(self) -> SignalSample:
        return next(self.samples)

    def close(self) -> None:
        self.closed = True


class RecordingHealth:
    def __init__(self) -> None:
        self.events: list[str] = []

    def report(self, event: str) -> None:
        self.events.append(event)


class ResilienceTests(unittest.TestCase):
    def test_stale_reader_is_replaced_and_recovers(self) -> None:
        stale = FakeSource([SignalSample(None), SignalSample(None)])
        recovered = FakeSource([SignalSample(-4)])
        sources = iter((stale, recovered))
        health = RecordingHealth()
        source = RestartingSignalSource(lambda: next(sources), silence_limit=2, health=health)
        self.assertIsNone(source.read().rssi)
        self.assertIsNone(source.read().rssi)
        self.assertTrue(stale.closed)
        self.assertEqual(source.read().rssi, -4)
        self.assertEqual(health.events, ["SOURCE_STARTED", "SOURCE_STALE", "SOURCE_STARTED"])

    def test_disconnect_discards_reader_for_later_reconnection(self) -> None:
        disconnected = FakeSource([SignalSample(None, connected=False)])
        connected = FakeSource([SignalSample(-3)])
        sources = iter((disconnected, connected))
        source = RestartingSignalSource(lambda: next(sources))
        self.assertFalse(source.read().connected)
        self.assertTrue(disconnected.closed)
        self.assertEqual(source.read().rssi, -3)


if __name__ == "__main__":
    unittest.main()
