"""macOS IOBluetooth RSSI process exposed as a typed signal socket."""

from __future__ import annotations

from pathlib import Path
import queue
import subprocess
import threading

from bluetooth_proximity.models import SignalSample


class MacClassicRssiSource:
    def __init__(self, reader: Path, device_name: str, timeout: float = 1.5) -> None:
        self.timeout = timeout
        self.values: queue.Queue[SignalSample] = queue.Queue()
        self.process = subprocess.Popen(
            (str(reader), device_name),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self.thread = threading.Thread(target=self._read_output, name="mac-rssi-reader", daemon=True)
        self.thread.start()

    def read(self) -> SignalSample:
        try:
            return self.values.get(timeout=self.timeout)
        except queue.Empty:
            connected = False if self.process.poll() is not None else None
            return SignalSample(None, connected=connected)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def _read_output(self) -> None:
        if self.process.stdout is None:
            return
        for line in self.process.stdout:
            value = line.strip()
            if value == "missing":
                self.values.put(SignalSample(None, connected=False))
            elif value == "unknown":
                self.values.put(SignalSample(None))
            else:
                try:
                    self.values.put(SignalSample(int(value)))
                except ValueError:
                    continue
