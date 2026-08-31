"""Windows menu boundary; the GUI owns refresh scheduling."""

from __future__ import annotations

from vibebar_modular.contracts import CommandResult


class WindowsMenuSocket:
    def refresh(self) -> CommandResult:
        return CommandResult(0)
