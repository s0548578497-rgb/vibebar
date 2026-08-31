"""Replaceable language component backed by locale JSON files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol


class LanguageCatalog(Protocol):
    @property
    def code(self) -> str: ...
    def text(self, key: str) -> str: ...


@dataclass(frozen=True, slots=True)
class JsonLanguageCatalog:
    code: str
    values: dict[str, str]

    def text(self, key: str) -> str:
        return self.values.get(key, key)


class LanguageController:
    def __init__(self, locale_dir: Path, settings_file: Path) -> None:
        self.locale_dir = locale_dir
        self.settings_file = settings_file
        self.codes = ("he", "ru", "en")
        self.catalog = self._load(self._saved_code())

    def switch(self) -> JsonLanguageCatalog:
        index = (self.codes.index(self.catalog.code) + 1) % len(self.codes)
        self.catalog = self._load(self.codes[index])
        self._save(self.catalog.code)
        return self.catalog

    def _load(self, code: str) -> JsonLanguageCatalog:
        path = self.locale_dir / f"{code}.json"
        values = json.loads(path.read_text(encoding="utf-8"))
        return JsonLanguageCatalog(code, values)

    def _saved_code(self) -> str:
        if not self.settings_file.exists():
            return "he"
        try:
            code = json.loads(self.settings_file.read_text(encoding="utf-8")).get("language", "he")
        except (OSError, json.JSONDecodeError):
            return "he"
        return code if code in self.codes else "he"

    def _save(self, code: str) -> None:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps({"language": code}, indent=2), encoding="utf-8")
