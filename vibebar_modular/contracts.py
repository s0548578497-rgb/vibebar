"""Typed contracts for external boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class CommandRunner(Protocol):
    def run(self, arguments: Sequence[str]) -> CommandResult: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class EntrySocket(Protocol):
    def submit(self, text: str) -> CommandResult: ...


class ClipboardSocket(Protocol):
    def add_current(self) -> CommandResult: ...
    def copy(self, index: int) -> CommandResult: ...
    def show(self, index: int) -> CommandResult: ...


class RecycleBinSocket(Protocol):
    def delete_clipboard_item(self, index: int) -> CommandResult: ...
    def clear_clipboard(self) -> CommandResult: ...


class DigestSocket(Protocol):
    def build_day(self, rebuild: bool = False) -> CommandResult: ...
    def build_week(self, end: date | None = None) -> CommandResult: ...
    def publish_day(self, day: date | None = None) -> CommandResult: ...


class MenuSocket(Protocol):
    def refresh(self) -> CommandResult: ...


class FileOpenerSocket(Protocol):
    def open(self, path: Path) -> CommandResult: ...


class Paths(Protocol):
    @property
    def repository(self) -> Path: ...
