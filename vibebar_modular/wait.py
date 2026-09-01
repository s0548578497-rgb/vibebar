"""Shared waiting policy; adapters must not implement ad-hoc retry loops."""

from __future__ import annotations

import time
from typing import Callable


def wait_until(
    predicate: Callable[[], bool],
    timeout: float,
    interval: float = 0.1,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    deadline = clock() + timeout
    while clock() < deadline:
        if predicate():
            return True
        sleep(interval)
    return predicate()
