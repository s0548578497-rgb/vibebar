"""Replaceable Bluetooth device discovery and selection contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from collections.abc import Callable
from typing import Protocol

from .models import SignalSample


@dataclass(frozen=True, slots=True)
class BluetoothDevice:
    identifier: str
    name: str
    connected: bool = False


class BluetoothDeviceProvider(Protocol):
    def devices(self) -> tuple[BluetoothDevice, ...]: ...


class NullBluetoothDeviceProvider:
    def devices(self) -> tuple[BluetoothDevice, ...]:
        return ()


class SelectedDeviceStore(Protocol):
    def load(self) -> BluetoothDevice | None: ...
    def save(self, device: BluetoothDevice) -> None: ...


class NullSelectedDeviceStore:
    def load(self) -> BluetoothDevice | None:
        return None

    def save(self, device: BluetoothDevice) -> None:
        return None


class JsonSelectedDeviceStore:
    def __init__(self, path: Path, fallback: BluetoothDevice | None = None) -> None:
        self.path = path
        self.fallback = fallback

    def load(self) -> BluetoothDevice | None:
        if not self.path.exists():
            return self.fallback
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return BluetoothDevice(str(value["identifier"]), str(value["name"]), bool(value.get("connected", False)))
        except (OSError, json.JSONDecodeError, KeyError):
            return self.fallback

    def save(self, device: BluetoothDevice) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".new")
        temporary.write_text(json.dumps(asdict(device), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)


class ClosableSource(Protocol):
    def read(self) -> SignalSample: ...
    def close(self) -> None: ...


class SwitchingSignalSource:
    """Swap the live sensor when the persisted device selection changes."""

    def __init__(self, store: SelectedDeviceStore, factory: Callable[[BluetoothDevice], ClosableSource]) -> None:
        self.store = store
        self.factory = factory
        self.selected: BluetoothDevice | None = None
        self.source: ClosableSource | None = None

    def read(self) -> SignalSample:
        selected = self.store.load()
        if self._key(selected) != self._key(self.selected):
            self.close()
            self.selected = selected
            self.source = self.factory(selected) if selected is not None else None
        return self.source.read() if self.source is not None else SignalSample(None)

    def close(self) -> None:
        if self.source is not None:
            self.source.close()
            self.source = None

    @staticmethod
    def _key(device: BluetoothDevice | None) -> tuple[str, str] | None:
        return (device.identifier, device.name) if device is not None else None
