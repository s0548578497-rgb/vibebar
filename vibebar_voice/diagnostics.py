"""Privacy-preserving voice diagnostics that never store spoken text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading
from typing import Protocol

from vibebar_modular.contracts import Clock


Scalar = str | int | float | bool | None


class DiagnosticLog(Protocol):
    def event(self, name: str, **fields: Scalar) -> None: ...


class NullDiagnosticLog:
    def event(self, name: str, **fields: Scalar) -> None:
        return None


class JsonLineDiagnosticLog:
    def __init__(self, path: Path, clock: Clock) -> None:
        self.path = path
        self.clock = clock
        self.lock = threading.Lock()

    def event(self, name: str, **fields: Scalar) -> None:
        record = {"at": self.clock.now().isoformat(timespec="milliseconds"), "event": name, **fields}
        try:
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError:
            return None


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
