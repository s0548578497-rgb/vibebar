from __future__ import annotations

from typing import Protocol

from .models import SignalSample


class SignalSource(Protocol):
    def read(self) -> SignalSample: ...


class NullSignalSource:
    def read(self) -> SignalSample:
        return SignalSample(None)
