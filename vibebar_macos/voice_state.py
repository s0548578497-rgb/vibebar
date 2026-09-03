"""Persistent, replaceable switch for the macOS background listener."""

from __future__ import annotations

import json
from pathlib import Path


class VoiceState:
    def __init__(self, path: Path) -> None:
        self.path = path

    def enabled(self) -> bool:
        if not self.path.exists():
            return True
        try:
            return bool(json.loads(self.path.read_text(encoding="utf-8")).get("enabled", True))
        except (OSError, json.JSONDecodeError):
            return True

    def toggle(self) -> bool:
        enabled = not self.enabled()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"enabled": enabled}, indent=2), encoding="utf-8")
        return enabled
