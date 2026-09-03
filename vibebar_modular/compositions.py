"""Feature compositions are the sole source of visible capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    ADD_ENTRY = "add_entry"
    CAPTURE_CLIPBOARD = "capture_clipboard"
    VIEW_CLIPBOARD = "view_clipboard"
    COPY_CLIPBOARD = "copy_clipboard"
    DELETE_CLIPBOARD = "delete_clipboard"
    CLEAR_CLIPBOARD = "clear_clipboard"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"
    PUBLISH_DIGEST = "publish_digest"
    OPEN_JOURNAL = "open_journal"
    VOICE_INPUT = "voice_input"


@dataclass(frozen=True, slots=True)
class Composition:
    name: str
    actions: frozenset[Action]

    def contains(self, action: Action) -> bool:
        return action in self.actions


PILOT = Composition(
    "pilot",
    frozenset({Action.ADD_ENTRY, Action.CAPTURE_CLIPBOARD, Action.VIEW_CLIPBOARD, Action.COPY_CLIPBOARD}),
)

WINDOWS = Composition(
    "windows",
    frozenset({
        Action.ADD_ENTRY,
        Action.CAPTURE_CLIPBOARD,
        Action.VIEW_CLIPBOARD,
        Action.COPY_CLIPBOARD,
        Action.DELETE_CLIPBOARD,
        Action.CLEAR_CLIPBOARD,
        Action.DAILY_DIGEST,
        Action.WEEKLY_DIGEST,
        Action.PUBLISH_DIGEST,
        Action.OPEN_JOURNAL,
        Action.VOICE_INPUT,
    }),
)

MACOS = Composition("macos", frozenset(Action))
FULL = Composition("full", frozenset(Action))


def get_composition(name: str) -> Composition:
    compositions = {PILOT.name: PILOT, WINDOWS.name: WINDOWS, MACOS.name: MACOS, FULL.name: FULL}
    if name not in compositions:
        raise ValueError(f"unknown composition: {name}")
    return compositions[name]
