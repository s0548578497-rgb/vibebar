from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .models import SignalSample


class ClosableSignalSource(Protocol):
    def read(self) -> SignalSample: ...
    def close(self) -> None: ...


class SourceHealthSink(Protocol):
    def report(self, event: str) -> None: ...


class NullSourceHealthSink:
    def report(self, event: str) -> None:
        return


class RestartingSignalSource:
    """Replace a reader whose live process has stopped producing samples."""

    def __init__(
        self,
        factory: Callable[[], ClosableSignalSource],
        silence_limit: int = 5,
        health: SourceHealthSink | None = None,
    ) -> None:
        if silence_limit < 1:
            raise ValueError("silence_limit must be positive")
        self.factory = factory
        self.silence_limit = silence_limit
        self.health = health or NullSourceHealthSink()
        self.source: ClosableSignalSource | None = None
        self.silence_count = 0

    def read(self) -> SignalSample:
        if self.source is None:
            self.source = self.factory()
            self.health.report("SOURCE_STARTED")
        sample = self.source.read()
        if sample.connected is False:
            self._discard("SOURCE_DISCONNECTED")
            return sample
        if sample.rssi is not None:
            self.silence_count = 0
            return sample
        self.silence_count += 1
        if self.silence_count >= self.silence_limit:
            self._discard("SOURCE_STALE")
        return sample

    def close(self) -> None:
        self._discard("SOURCE_CLOSED")

    def _discard(self, event: str) -> None:
        if self.source is not None:
            self.source.close()
            self.source = None
        self.silence_count = 0
        self.health.report(event)
