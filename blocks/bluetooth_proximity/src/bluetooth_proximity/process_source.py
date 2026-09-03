"""Shared lifecycle for native RSSI readers that emit one value per line."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import queue
import subprocess
import threading

from .models import SignalSample


LineParser = Callable[[str], SignalSample | None]


class LineProcessSignalSource:
    """Expose a line-oriented helper process as a blocking signal source."""

    def __init__(
        self,
        command: Sequence[str],
        parser: LineParser,
        timeout: float,
        thread_name: str,
        creationflags: int = 0,
    ) -> None:
        self.timeout = timeout
        self.parser = parser
        self.values: queue.Queue[SignalSample] = queue.Queue()
        self.process = subprocess.Popen(
            tuple(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=creationflags,
        )
        self.thread = threading.Thread(target=self._read_output, name=thread_name, daemon=True)
        self.thread.start()

    def read(self) -> SignalSample:
        try:
            return self.values.get(timeout=self.timeout)
        except queue.Empty:
            # Process death is different from a temporarily missing RSSI value:
            # the restart wrapper may replace only an explicitly dead reader.
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
            sample = self.parser(line.strip())
            if sample is not None:
                self.values.put(sample)
