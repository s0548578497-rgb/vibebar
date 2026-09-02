from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from bluetooth_proximity.calibration import calibrate
from bluetooth_proximity.contracts import NullSignalSource
from bluetooth_proximity.engine import ProximityEngine
from bluetooth_proximity.models import ProximityConfig, ProximityState, SignalSample
from bluetooth_proximity.monitor import ProximityMonitor
from bluetooth_proximity.config_store import JsonConfigStore, NullConfigStore


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ProximityEngine(ProximityConfig(window_size=3, confirmations=2, missing_limit=3))

    def feed(self, *values: int | None) -> ProximityState:
        state = ProximityState.UNKNOWN
        for value in values:
            state = self.engine.update(SignalSample(value))
        return state

    def test_requires_confirmations_before_near(self) -> None:
        self.assertEqual(self.feed(-55), ProximityState.UNKNOWN)
        self.assertEqual(self.feed(-55), ProximityState.NEAR)

    def test_median_rejects_single_drop(self) -> None:
        self.feed(-55, -55)
        self.assertEqual(self.feed(-95, -55), ProximityState.NEAR)

    def test_far_uses_separate_threshold(self) -> None:
        self.feed(-55, -55)
        self.assertEqual(self.feed(-90, -90, -90), ProximityState.FAR)

    def test_missing_becomes_unknown_after_limit(self) -> None:
        self.feed(-55, -55)
        self.assertEqual(self.feed(None, None), ProximityState.NEAR)
        self.assertEqual(self.feed(None), ProximityState.UNKNOWN)

    def test_null_source_is_safe(self) -> None:
        changes: list[ProximityState] = []
        monitor = ProximityMonitor(NullSignalSource(), self.engine, changes.append)
        self.assertEqual(monitor.poll(), ProximityState.UNKNOWN)
        self.assertEqual(changes, [])

    def test_calibration_places_thresholds_between_zones(self) -> None:
        config = calibrate([-50, -51, -49], [-85, -84, -86])
        self.assertGreater(config.near_threshold, config.far_threshold)
        self.assertGreater(config.near_threshold, -85)
        self.assertLess(config.near_threshold, -50)

    def test_config_store_is_replaceable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonConfigStore(Path(directory) / "profile.json")
            expected = ProximityConfig(near_threshold=-5, far_threshold=-10)
            store.save(expected)
            self.assertEqual(store.load(), expected)
        self.assertEqual(NullConfigStore().load(), ProximityConfig())


if __name__ == "__main__":
    unittest.main()
