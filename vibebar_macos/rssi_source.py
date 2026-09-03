"""macOS command adapter for the shared line-oriented RSSI process."""

from __future__ import annotations

from pathlib import Path

from bluetooth_proximity.models import SignalSample
from bluetooth_proximity.process_source import LineProcessSignalSource


class MacClassicRssiSource(LineProcessSignalSource):
    """Read Classic Bluetooth RSSI from the native Swift helper."""

    def __init__(self, reader: Path, device_name: str, timeout: float = 1.5) -> None:
        super().__init__((str(reader), device_name), _parse_macos_line, timeout, "mac-rssi-reader")


def _parse_macos_line(value: str) -> SignalSample | None:
    if value == "missing":
        return SignalSample(None, connected=False)
    if value == "unknown":
        return SignalSample(None)
    try:
        return SignalSample(int(value))
    except ValueError:
        return None
