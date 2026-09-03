"""Persistent selection between interchangeable macOS voice pipelines."""

from __future__ import annotations

from enum import Enum
import json
from pathlib import Path


class VoiceBackend(str, Enum):
    ORIGINAL = "original"
    CPP = "cpp"
    OFF = "off"

    def label(self, language: str) -> str:
        labels = {
            "he": {self.ORIGINAL: "המסלול המקורי — Superwhisper + macrowhisper", self.CPP: "Whisper מקומי — whisper.cpp", self.OFF: "קול כבוי"},
            "ru": {self.ORIGINAL: "Оригинальный — Superwhisper + macrowhisper", self.CPP: "Локальный Whisper — whisper.cpp", self.OFF: "Голос выключен"},
            "en": {self.ORIGINAL: "Original — Superwhisper + macrowhisper", self.CPP: "Local Whisper — whisper.cpp", self.OFF: "Voice off"},
        }
        return labels.get(language, labels["en"])[self]


class VoiceBackendStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> VoiceBackend:
        if not self.path.exists():
            return VoiceBackend.ORIGINAL
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return VoiceBackend.ORIGINAL
        if "backend" in payload:
            try:
                return VoiceBackend(str(payload["backend"]))
            except ValueError:
                return VoiceBackend.ORIGINAL
        return VoiceBackend.CPP if payload.get("enabled", True) else VoiceBackend.OFF

    def save(self, backend: VoiceBackend) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"backend": backend.value}, indent=2), encoding="utf-8")
