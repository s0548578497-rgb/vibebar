"""Shared local task clock over journal timestamps; no polling of business data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Protocol

from vibebar_modular.contracts import Clock


@dataclass(frozen=True, slots=True)
class TaskTimerState:
    task: str = ""
    started_at: datetime | None = None

    def display(self, now: datetime) -> str:
        if self.started_at is None:
            return "—"
        minutes = max(0, int((now - self.started_at).total_seconds() // 60))
        duration = f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"
        return f"{self.task} · {duration}"


class TaskTimerSocket(Protocol):
    def load(self) -> TaskTimerState: ...


class NullTaskTimerSocket:
    def load(self) -> TaskTimerState:
        return TaskTimerState()


@dataclass(frozen=True, slots=True)
class JournalTaskTimerSocket:
    journal: Path
    clock: Clock

    def load(self) -> TaskTimerState:
        if not self.journal.exists():
            return TaskTimerState()
        now = self.clock.now()
        last = self._last_timed_entry(now.strftime("%Y-%m-%d"))
        if last is None or last[1].startswith("⏸"):
            return TaskTimerState()
        hour, minute = (int(part) for part in last[0].split(":"))
        started = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        task = re.sub(r"\s*<!--.*?-->\s*$", "", last[1])
        return TaskTimerState(task, started)

    def _last_timed_entry(self, day: str) -> tuple[str, str] | None:
        in_day = False
        last: tuple[str, str] | None = None
        for raw in self.journal.read_text(encoding="utf-8").splitlines():
            if raw == f"## {day}":
                in_day = True
                continue
            if raw.startswith("## "):
                in_day = False
            match = re.match(r"^- (\d{2}:\d{2}) · (.*)$", raw) if in_day else None
            if match and not match.group(2).startswith(("💡", "❗", "✅")):
                last = match.group(1), match.group(2)
        return last
