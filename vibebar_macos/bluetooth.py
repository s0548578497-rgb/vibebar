"""Connection-only macOS Bluetooth socket; it never pretends to provide RSSI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Protocol

from vibebar_modular.contracts import CommandRunner


class BluetoothConnectionSocket(Protocol):
    def connected(self) -> bool | None: ...


class NullBluetoothConnectionSocket:
    def connected(self) -> bool | None:
        return None


@dataclass(frozen=True, slots=True)
class SystemProfilerBluetoothSocket:
    runner: CommandRunner
    device_name: str

    def connected(self) -> bool | None:
        arguments = ("system_profiler", "SPBluetoothDataType", "-json", "-detailLevel", "mini")
        result = self.runner.run(arguments)
        if not result.succeeded:
            return None
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        device = _find_device(payload, self.device_name.casefold())
        return _connected_value(device) if device is not None else False


def _find_device(value: object, wanted: str) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).casefold() == wanted and isinstance(child, Mapping):
                return child
            found = _find_device(child, wanted)
            if found is not None:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            found = _find_device(child, wanted)
            if found is not None:
                return found
    return None


def _connected_value(device: Mapping[str, object]) -> bool | None:
    value = device.get("device_connected")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        folded = value.casefold()
        if folded in {"yes", "true", "attrib_yes"}:
            return True
        if folded in {"no", "false", "attrib_no"}:
            return False
    return None
