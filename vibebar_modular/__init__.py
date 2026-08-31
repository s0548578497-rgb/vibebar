"""Socket-based wrappers around the unchanged VibeBar implementation."""

from .assembly import Assembly, assemble
from .compositions import Composition, get_composition
from .sockets import SocketSet, build_sockets

__all__ = [
    "Assembly",
    "Composition",
    "SocketSet",
    "assemble",
    "build_sockets",
    "get_composition",
]
