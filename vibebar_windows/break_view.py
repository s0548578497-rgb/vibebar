"""Read pause entries without changing the legacy menu renderer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Protocol

from vibebar_modular.contracts import Clock

from .view_model import ActivityItem, MenuViewSocket, VibeBarView


class BreakViewSocket(Protocol):
    def load(self) -> tuple[ActivityItem, ...]: ...


class NullBreakViewSocket:
    def load(self) -> tuple[ActivityItem, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class JournalBreakViewSocket:
    journal: Path
    clock: Clock

    def load(self) -> tuple[ActivityItem, ...]:
        if not self.journal.exists():
            return ()
        today = f"## {self.clock.now():%Y-%m-%d}"
        active = False
        result: list[ActivityItem] = []
        for line in self.journal.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                active = line == today
                continue
            match = re.match(r"^- (\d{2}:\d{2}) · (⏸.*?)(?:\s*<!--.*)?$", line) if active else None
            if match:
                result.append(ActivityItem(match.group(1), match.group(2).strip()))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class CombinedMenuViewSocket:
    inner: MenuViewSocket
    breaks: BreakViewSocket

    def load(self) -> VibeBarView:
        view = self.inner.load()
        breaks = self.breaks.load()
        timeline = tuple(sorted((*view.tasks, *breaks), key=lambda item: item.time, reverse=True))
        return VibeBarView(view.current, timeline, view.ideas, view.todos, view.clipboard, breaks)
