"""Identity adapters that delegate to the original scripts unchanged."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .contracts import CommandResult, CommandRunner


@dataclass(frozen=True, slots=True)
class LegacyEntrySocket:
    root: Path
    runner: CommandRunner

    def submit(self, text: str) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-add.sh"), text))


@dataclass(frozen=True, slots=True)
class LegacyClipboardSocket:
    root: Path
    runner: CommandRunner

    def add_current(self) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-buf.sh"), "add"))

    def copy(self, index: int) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-buf.sh"), "copy", str(index)))

    def show(self, index: int) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-buf.sh"), "show", str(index)))


@dataclass(frozen=True, slots=True)
class LegacyRecycleBin:
    root: Path
    runner: CommandRunner

    def delete_clipboard_item(self, index: int) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-buf.sh"), "del", str(index)))

    def clear_clipboard(self) -> CommandResult:
        return self.runner.run((str(self.root / "bin" / "vibebar-buf.sh"), "clear"))


@dataclass(frozen=True, slots=True)
class LegacyDigestSocket:
    root: Path
    runner: CommandRunner

    def build_day(self, rebuild: bool = False) -> CommandResult:
        args = [str(self.root / "bin" / "vibebar-day.sh")]
        if rebuild:
            args.append("--rebuild")
        return self.runner.run(args)

    def build_week(self, end: date | None = None) -> CommandResult:
        args = [str(self.root / "bin" / "vibebar-week.sh")]
        if end is not None:
            args.append(end.isoformat())
        return self.runner.run(args)

    def publish_day(self, day: date | None = None) -> CommandResult:
        args = [str(self.root / "bin" / "vibebar-push-vault.sh")]
        if day is not None:
            args.append(day.isoformat())
        return self.runner.run(args)


@dataclass(frozen=True, slots=True)
class LegacyMenuSocket:
    runner: CommandRunner

    def refresh(self) -> CommandResult:
        return self.runner.run(("open", "swiftbar://refreshallplugins"))
