"""Feature compositions are the sole source of visible capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    ADD_ENTRY = "add_entry"
    VIEW_CLIPBOARD = "view_clipboard"
    COPY_CLIPBOARD = "copy_clipboard"
    DELETE_CLIPBOARD = "delete_clipboard"
    CLEAR_CLIPBOARD = "clear_clipboard"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"
    PUBLISH_DIGEST = "publish_digest"


@dataclass(frozen=True, slots=True)
class Composition:
    name: str
    actions: frozenset[Action]

    def contains(self, action: Action) -> bool:
        return action in self.actions


PILOT = Composition(
    "pilot",
    frozenset({Action.ADD_ENTRY, Action.VIEW_CLIPBOARD, Action.COPY_CLIPBOARD}),
)

FULL = Composition("full", frozenset(Action))


def get_composition(name: str) -> Composition:
    compositions = {PILOT.name: PILOT, FULL.name: FULL}
    if name not in compositions:
        raise ValueError(f"unknown composition: {name}")
    return compositions[name]
