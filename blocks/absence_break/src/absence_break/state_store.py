"""Crash-safe JSON persistence for pending and confirmed absence."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .models import AbsenceState, PresenceStatus


class JsonStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> AbsenceState:
        if not self.path.exists():
            return AbsenceState()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            pending = value.get("pending_since")
            cause = value.get("cause")
            return AbsenceState(
                pending_since=None if pending is None else datetime.fromisoformat(pending),
                cause=None if cause is None else PresenceStatus(cause),
                confirmed=bool(value.get("confirmed")),
            )
        except (OSError, ValueError, json.JSONDecodeError):
            return AbsenceState()

    def save(self, state: AbsenceState) -> None:
        value = {
            "pending_since": None if state.pending_since is None else state.pending_since.isoformat(),
            "cause": None if state.cause is None else state.cause.value,
            "confirmed": state.confirmed,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, indent=2)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        temporary.write_text(payload, encoding="utf-8")
        try:
            temporary.replace(self.path)
        except PermissionError:
            # Windows indexers may briefly hold the existing file open.  A
            # direct write is less crash-safe, but losing monitor state or the
            # whole background service is worse than that narrow fallback.
            self.path.write_text(payload, encoding="utf-8")
            temporary.unlink(missing_ok=True)
