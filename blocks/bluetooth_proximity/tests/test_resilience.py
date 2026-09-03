from __future__ import annotations

import unittest

from bluetooth_proximity.models import SignalSample
from bluetooth_proximity.resilience import ExponentialReconnectPolicy, RestartingSignalSource


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


class FakeMonotonic:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


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

    def test_backoff_avoids_reader_and_log_restart_loops(self) -> None:
        clock = FakeMonotonic()
        sources: list[FakeSource] = []
        health = RecordingHealth()

        def factory() -> FakeSource:
            source = FakeSource([SignalSample(None, connected=False)])
            sources.append(source)
            return source

        source = RestartingSignalSource(
            factory, health=health, reconnect=ExponentialReconnectPolicy((2.0, 5.0)), monotonic=clock
        )
        source.read()
        source.read()
        self.assertEqual(len(sources), 1)
        self.assertEqual(health.events.count("SOURCE_DISCONNECTED"), 1)
        clock.value = 2.0
        source.read()
        self.assertEqual(len(sources), 2)


if __name__ == "__main__":
    unittest.main()
