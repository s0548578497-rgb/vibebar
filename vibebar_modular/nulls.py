"""Safe sealed plates for every socket contract."""

from __future__ import annotations

from datetime import date

from .contracts import CommandResult


def _sealed() -> CommandResult:
    return CommandResult(0)


class NullEntrySocket:
    """Reject input so the upstream recording remains available for recovery."""

    def submit(self, text: str) -> CommandResult:
        return CommandResult(78, stderr="entry socket is sealed")


class NullClipboardSocket:
    def add_current(self) -> CommandResult:
        return _sealed()

    def copy(self, index: int) -> CommandResult:
        return _sealed()

    def show(self, index: int) -> CommandResult:
        return _sealed()


class NullRecycleBin:
    """Forgetting to wire deletion must preserve all data."""

    def delete_clipboard_item(self, index: int) -> CommandResult:
        return _sealed()

    def clear_clipboard(self) -> CommandResult:
        return _sealed()


class NullDigestSocket:
    def build_day(self, rebuild: bool = False) -> CommandResult:
        return _sealed()

    def build_week(self, end: date | None = None) -> CommandResult:
        return _sealed()

    def publish_day(self, day: date | None = None) -> CommandResult:
        return _sealed()


class NullMenuSocket:
    def refresh(self) -> CommandResult:
        return _sealed()
