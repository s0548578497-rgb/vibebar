"""Adapt the unchanged SwiftBar output into a Windows presentation model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Protocol

from vibebar_modular.contracts import CommandRunner


@dataclass(frozen=True, slots=True)
class ActivityItem:
    time: str
    text: str


@dataclass(frozen=True, slots=True)
class ClipboardItem:
    display_index: int
    source_index: int
    preview: str


@dataclass(frozen=True, slots=True)
class VibeBarView:
    current: str
    tasks: tuple[ActivityItem, ...]
    ideas: tuple[ActivityItem, ...]
    todos: tuple[ActivityItem, ...]
    clipboard: tuple[ClipboardItem, ...]
    breaks: tuple[ActivityItem, ...] = ()


class MenuViewSocket(Protocol):
    def load(self) -> VibeBarView: ...


@dataclass(frozen=True, slots=True)
class LegacyMenuViewSocket:
    root: Path
    runner: CommandRunner

    def load(self) -> VibeBarView:
        script = self.root / "windows" / "bin" / "render_menu"
        result = self.runner.run((str(script),))
        if not result.succeeded:
            raise RuntimeError(result.stderr.strip() or "legacy menu rendering failed")
        return parse_swiftbar_output(result.stdout)


def parse_swiftbar_output(output: str) -> VibeBarView:
    sections = _sections(output.splitlines())
    current = sections[0][0].removeprefix("▸ ").strip() if sections and sections[0] else "—"
    return VibeBarView(
        current=current,
        tasks=_activity_items(_section(sections, 1)),
        ideas=_activity_items(_section(sections, 2)),
        todos=_activity_items(_section(sections, 3)),
        clipboard=_clipboard_items(_section(sections, 4)),
    )


def _sections(lines: list[str]) -> list[list[str]]:
    sections: list[list[str]] = [[]]
    for line in lines:
        if line == "---":
            sections.append([])
        else:
            sections[-1].append(line)
    return sections


def _section(sections: list[list[str]], index: int) -> list[str]:
    return sections[index] if index < len(sections) else []


def _activity_items(lines: list[str]) -> tuple[ActivityItem, ...]:
    items: list[ActivityItem] = []
    for line in lines[1:]:
        label = line.split("|", 1)[0].strip()
        match = re.match(r"^(\d{1,2}:\d{2})\s+(.*)$", label)
        if match:
            text = re.sub(r"\s*<!--.*?-->\s*$", "", match.group(2)).strip()
            items.append(ActivityItem(match.group(1), text))
    return tuple(items)


def _clipboard_items(lines: list[str]) -> tuple[ClipboardItem, ...]:
    items: list[ClipboardItem] = []
    for line in lines[2:]:
        if line.startswith(("👁", "✕", "--", "-----")):
            break
        label, _, parameters = line.partition("|")
        match = re.match(r"^(\d+)\s+(.*)$", label.strip())
        source = re.search(r"param2=(\d+)", parameters)
        if match and source:
            items.append(ClipboardItem(int(match.group(1)), int(source.group(1)), match.group(2).strip()))
    return tuple(items)
