from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Protocol

from .models import ProximityConfig


class ConfigStore(Protocol):
    def load(self) -> ProximityConfig: ...


class NullConfigStore:
    def load(self) -> ProximityConfig:
        return ProximityConfig()


class JsonConfigStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> ProximityConfig:
        values = json.loads(self.path.read_text(encoding="utf-8"))
        config = ProximityConfig(**values)
        config.validate()
        return config

    def save(self, config: ProximityConfig) -> None:
        config.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
