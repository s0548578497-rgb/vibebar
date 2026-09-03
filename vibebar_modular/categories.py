"""Shared post-hoc numbered task categories, independent of transcription text."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from typing import Protocol

from vibebar_modular.contracts import Clock


@dataclass(frozen=True, slots=True)
class Category:
    number: int
    names: dict[str, str]

    def label(self, language: str) -> str:
        return f"{self.number} — {self.names.get(language, self.names['en'])}"


@dataclass(frozen=True, slots=True)
class TimedTask:
    key: str
    day: str
    time: str
    text: str
    minutes: int
    category: int | None


class ClassificationRepository(Protocol):
    def load(self) -> dict[str, int]: ...
    def assign(self, key: str, category: int) -> None: ...


class NullClassificationRepository:
    def load(self) -> dict[str, int]:
        return {}

    def assign(self, key: str, category: int) -> None:
        return None


class JsonClassificationRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, int]:
        if not self.path.exists():
            return {}
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {str(key): int(value) for key, value in values.items()}

    def assign(self, key: str, category: int) -> None:
        values = self.load()
        values[key] = category
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".new")
        temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)


class CategoryService:
    def __init__(self, journal: Path, catalog: tuple[Category, ...], store: ClassificationRepository, clock: Clock) -> None:
        self.journal = journal
        self.catalog = catalog
        self.store = store
        self.clock = clock

    def tasks(self, days: int = 1) -> tuple[TimedTask, ...]:
        now = self.clock.now()
        first = (now.date() - timedelta(days=days - 1)).isoformat()
        assignments = self.store.load()
        events = self._events(first, now.date().isoformat())
        rows: list[TimedTask] = []
        for index, event in enumerate(events):
            end = events[index + 1][0] if index + 1 < len(events) and events[index + 1][1] == event[1] else None
            if end is None and event[1] == now.date().isoformat():
                end = now
            if end is None or event[3].startswith("⏸"):
                continue
            minutes = max(0, int((end - event[0]).total_seconds() // 60))
            key = self._key(event[1], event[2], event[3])
            rows.append(TimedTask(key, event[1], event[2], event[3], minutes, assignments.get(key)))
        return tuple(rows)

    def assign(self, key: str, category: int) -> None:
        if category in {item.number for item in self.catalog}:
            self.store.assign(key, category)

    def summary(self, days: int, language: str) -> str:
        totals: dict[int, int] = {}
        for task in self.tasks(days):
            if task.category is not None:
                totals[task.category] = totals.get(task.category, 0) + task.minutes
        heading = {"he": "סיכום לפי קטגוריה", "ru": "Итоги по категориям", "en": "Category totals"}.get(language, "Category totals")
        lines = [f"### {heading}", "", "| # | Category | Time |", "|---|---|---|"]
        for category in self.catalog:
            minutes = totals.get(category.number, 0)
            if minutes:
                lines.append(f"| {category.number} | {category.names.get(language, category.names['en'])} | {minutes // 60}h {minutes % 60:02d}m |")
        if len(lines) == 4:
            lines.append("| — | — | 0m |")
        return "\n".join(lines)

    def _events(self, first: str, last: str) -> list[tuple[datetime, str, str, str]]:
        if not self.journal.exists():
            return []
        current = ""
        rows: list[tuple[datetime, str, str, str]] = []
        for line in self.journal.read_text(encoding="utf-8").splitlines():
            day = re.match(r"^## (\d{4}-\d{2}-\d{2})$", line)
            if day:
                current = day.group(1)
                continue
            match = re.match(r"^- (\d{2}:\d{2}) · (.*)$", line)
            if first <= current <= last and match and not match.group(2).startswith(("💡", "❗")):
                moment = datetime.strptime(f"{current} {match.group(1)}", "%Y-%m-%d %H:%M")
                rows.append((moment, current, match.group(1), match.group(2)))
        return rows

    @staticmethod
    def _key(day: str, time: str, text: str) -> str:
        return f"{day}|{time}|{' '.join(text.split())}"


def load_categories(path: Path) -> tuple[Category, ...]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(Category(int(row["id"]), {code: str(row[code]) for code in ("he", "ru", "en")}) for row in rows)
