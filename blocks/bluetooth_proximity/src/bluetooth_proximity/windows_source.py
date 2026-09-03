from __future__ import annotations

from pathlib import Path
import queue
import subprocess
import threading

from .models import SignalSample


class WindowsClassicRssiSource:
    def __init__(
        self, reader: Path, device_name: str, timeout: float = 1.5, absolute: bool = False
    ) -> None:
        self.timeout = timeout
        self.values: queue.Queue[SignalSample] = queue.Queue()
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        self.process = subprocess.Popen(
            (str(reader), device_name, "500", "absolute" if absolute else "relative"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=flags,
        )
        self.thread = threading.Thread(target=self._read_output, name="classic-rssi-reader", daemon=True)
        self.thread.start()

    def read(self) -> SignalSample:
        try:
            return self.values.get(timeout=self.timeout)
        except queue.Empty:
            if self.process.poll() is not None:
                return SignalSample(None, connected=False)
            return SignalSample(None)

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
            else:
                try:
                    self.values.put(SignalSample(int(value)))
                except ValueError:
                    continue
