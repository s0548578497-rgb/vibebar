from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bluetooth_proximity.devices import BluetoothDevice, JsonSelectedDeviceStore, SwitchingSignalSource
from bluetooth_proximity.models import SignalSample
from bluetooth_proximity.windows_devices import _parse_devices


class FakeSource:
    def __init__(self, value: int) -> None:
        self.value = value
        self.closed = False

    def read(self) -> SignalSample:
        return SignalSample(self.value)

    def close(self) -> None:
        self.closed = True


class DeviceTests(unittest.TestCase):
    def test_selection_is_atomic_and_has_legacy_fallback(self) -> None:
        with TemporaryDirectory() as folder:
            fallback = BluetoothDevice("legacy", "JBL TUNE125BT")
            store = JsonSelectedDeviceStore(Path(folder) / "selected.json", fallback)
            self.assertEqual(store.load(), fallback)
            chosen = BluetoothDevice("id-2", "Other headset", True)
            store.save(chosen)
            self.assertEqual(store.load(), chosen)

    def test_switching_source_replaces_reader_when_selection_changes(self) -> None:
        with TemporaryDirectory() as folder:
            store = JsonSelectedDeviceStore(Path(folder) / "selected.json")
            first = BluetoothDevice("one", "First")
            second = BluetoothDevice("two", "Second")
            sources: list[FakeSource] = []

            def factory(device: BluetoothDevice) -> FakeSource:
                source = FakeSource(1 if device.identifier == "one" else 2)
                sources.append(source)
                return source

            switching = SwitchingSignalSource(store, factory)
            store.save(first)
            self.assertEqual(switching.read().rssi, 1)
            store.save(second)
            self.assertEqual(switching.read().rssi, 2)
            self.assertTrue(sources[0].closed)

    def test_windows_discovery_parser_sorts_connected_first(self) -> None:
        payload = '[{"InstanceId":"b","FriendlyName":"Known","Status":"Unknown"},' \
                  '{"InstanceId":"a","FriendlyName":"Headset","Status":"OK"}]'
        devices = _parse_devices(payload)
        self.assertEqual([item.name for item in devices], ["Headset", "Known"])
        self.assertTrue(devices[0].connected)


if __name__ == "__main__":
    unittest.main()
