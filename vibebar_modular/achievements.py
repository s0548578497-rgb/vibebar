"""Independent achievement notes that never change the active task."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import threading
import time
from typing import Callable, Protocol

from .contracts import Clock, CommandResult


@dataclass(frozen=True, slots=True)
class Achievement:
    time: str
    text: str


class AchievementSocket(Protocol):
    def add(self, text: str) -> CommandResult: ...

    def load_today(self) -> tuple[Achievement, ...]: ...


class NullAchievementSocket:
    def add(self, text: str) -> CommandResult:
        return CommandResult(1, stderr="achievement socket is not connected")

    def load_today(self) -> tuple[Achievement, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class MarkdownAchievementSocket:
    journal: Path
    clock: Clock

    def add(self, text: str) -> CommandResult:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            return CommandResult(1, stderr="achievement is empty")
        now = self.clock.now()
        content = self.journal.read_text(encoding="utf-8") if self.journal.exists() else ""
        header = f"## {now:%Y-%m-%d}"
        prefix = "" if header in content.splitlines() else f"\n{header}\n"
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as stream:
            stream.write(f"{prefix}- {now:%H:%M} · ✅ {cleaned}\n")
        return CommandResult(0, stdout=cleaned)

    def load_today(self) -> tuple[Achievement, ...]:
        if not self.journal.exists():
            return ()
        active = False
        result: list[Achievement] = []
        for line in self.journal.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                active = line == f"## {self.clock.now():%Y-%m-%d}"
                continue
            match = re.match(r"^- (\d{2}:\d{2}) · ✅ (.+)$", line) if active else None
            if match:
                result.append(Achievement(match.group(1), match.group(2).strip()))
        return tuple(result)


class PendingAchievementCapture:
    def __init__(
        self, socket: AchievementSocket, lifetime: float = 45.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.socket = socket
        self.lifetime = lifetime
        self.monotonic = monotonic
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def arm(self) -> None:
        with self._lock:
            self._expires_at = self.monotonic() + self.lifetime

    def submit_if_armed(self, text: str) -> CommandResult | None:
        with self._lock:
            if self.monotonic() > self._expires_at:
                return None
            self._expires_at = 0.0
        return self.socket.add(text)
