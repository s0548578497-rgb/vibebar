"""Restart failed or silent native readers with bounded backoff."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
import time

from .models import SignalSample


class ClosableSignalSource(Protocol):
    def read(self) -> SignalSample: ...
    def close(self) -> None: ...


class SourceHealthSink(Protocol):
    def report(self, event: str) -> None: ...


class NullSourceHealthSink:
    def report(self, event: str) -> None:
        return


class ReconnectPolicy(Protocol):
    def delay(self, failures: int) -> float: ...


class ImmediateReconnectPolicy:
    def delay(self, failures: int) -> float:
        return 0.0


class ExponentialReconnectPolicy:
    def __init__(self, delays: tuple[float, ...] = (2.0, 5.0, 10.0, 30.0)) -> None:
        if not delays or any(value < 0 for value in delays):
            raise ValueError("delays must be non-negative")
        self.delays = delays

    def delay(self, failures: int) -> float:
        return self.delays[min(max(failures, 1) - 1, len(self.delays) - 1)]


class RestartingSignalSource:
    """Replace a reader whose live process has stopped producing samples."""

    def __init__(
        self,
        factory: Callable[[], ClosableSignalSource],
        silence_limit: int = 5,
        health: SourceHealthSink | None = None,
        reconnect: ReconnectPolicy | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if silence_limit < 1:
            raise ValueError("silence_limit must be positive")
        self.factory = factory
        self.silence_limit = silence_limit
        self.health = health or NullSourceHealthSink()
        self.reconnect = reconnect or ImmediateReconnectPolicy()
        self.monotonic = monotonic
        self.source: ClosableSignalSource | None = None
        self.silence_count = 0
        self.failures = 0
        self.retry_at = 0.0

    def read(self) -> SignalSample:
        if self.source is None:
            if self.monotonic() < self.retry_at:
                # During backoff, report no source rather than fabricate an
                # RSSI value that could be mistaken for physical distance.
                return SignalSample(None, connected=False)
            self.source = self.factory()
            self.health.report("SOURCE_STARTED")
        sample = self.source.read()
        if sample.connected is False:
            self.failures += 1
            self.retry_at = self.monotonic() + self.reconnect.delay(self.failures)
            self._discard("SOURCE_DISCONNECTED")
            return sample
        if sample.rssi is not None:
            self.silence_count = 0
            self.failures = 0
            self.retry_at = 0.0
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
