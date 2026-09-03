"""Persistent user-defined command aliases shared by every platform."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol


VALID_KINDS = ("task", "idea", "todo", "pause")


@dataclass(frozen=True, slots=True)
class CustomCommand:
    phrase: str
    kind: str


class CustomCommandRepository(Protocol):
    def load(self) -> tuple[CustomCommand, ...]: ...
    def add(self, phrase: str, kind: str) -> None: ...
    def delete(self, phrase: str) -> None: ...
    def aliases(self) -> dict[str, tuple[str, ...]]: ...


class NullCustomCommandStore:
    def load(self) -> tuple[CustomCommand, ...]:
        return ()

    def add(self, phrase: str, kind: str) -> None:
        return None

    def delete(self, phrase: str) -> None:
        return None

    def aliases(self) -> dict[str, tuple[str, ...]]:
        return {kind: () for kind in VALID_KINDS}


class CustomCommandStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> tuple[CustomCommand, ...]:
        if not self.path.exists():
            return ()
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ()
        return tuple(
            CustomCommand(str(row["phrase"]), str(row["kind"]))
            for row in rows
            if row.get("phrase") and row.get("kind") in VALID_KINDS
        )

    def add(self, phrase: str, kind: str) -> None:
        cleaned = " ".join(phrase.split())
        if not cleaned or kind not in VALID_KINDS:
            return
        rows = [row for row in self.load() if row.phrase.casefold() != cleaned.casefold()]
        rows.append(CustomCommand(cleaned, kind))
        self._save(rows)

    def delete(self, phrase: str) -> None:
        self._save([row for row in self.load() if row.phrase != phrase])

    def aliases(self) -> dict[str, tuple[str, ...]]:
        return {kind: tuple(row.phrase for row in self.load() if row.kind == kind) for kind in VALID_KINDS}

    def _save(self, rows: list[CustomCommand]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{"phrase": row.phrase, "kind": row.kind} for row in rows]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
