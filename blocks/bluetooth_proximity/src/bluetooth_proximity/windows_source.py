"""Windows command adapter for the shared line-oriented RSSI process."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import SignalSample
from .process_source import LineProcessSignalSource


class WindowsClassicRssiSource(LineProcessSignalSource):
    """Read normalized Classic Bluetooth RSSI from the Windows helper."""

    def __init__(
        self, reader: Path, device_name: str, timeout: float = 1.5, absolute: bool = False,
    ) -> None:
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        command = (str(reader), device_name, "500", "absolute" if absolute else "relative")
        super().__init__(command, _parse_windows_line, timeout, "classic-rssi-reader", flags)


def _parse_windows_line(value: str) -> SignalSample | None:
    if value == "missing":
        return SignalSample(None, connected=False)
    try:
        return SignalSample(int(value))
    except ValueError:
        return None
