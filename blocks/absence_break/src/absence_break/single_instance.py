from __future__ import annotations

from typing import Protocol


class InstanceGuard(Protocol):
    def acquire(self) -> bool: ...

    def close(self) -> None: ...


class NullInstanceGuard:
    def acquire(self) -> bool:
        return True

    def close(self) -> None:
        return None
