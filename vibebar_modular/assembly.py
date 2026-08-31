"""Composition-aware assembly keeps controls and connected sockets aligned."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .compositions import Action, Composition, get_composition
from .sockets import SocketSet, build_sockets


@dataclass(frozen=True, slots=True)
class Assembly:
    composition: Composition
    sockets: SocketSet

    @property
    def visible_actions(self) -> frozenset[Action]:
        return self.composition.actions


def assemble(root: Path, composition_name: str) -> Assembly:
    composition = get_composition(composition_name)
    deletion_connected = Action.DELETE_CLIPBOARD in composition.actions
    sockets = build_sockets(root, allow_deletion=deletion_connected)
    return Assembly(composition, sockets)
