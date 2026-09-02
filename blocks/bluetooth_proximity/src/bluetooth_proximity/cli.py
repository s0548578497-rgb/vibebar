from __future__ import annotations

import sys

from .engine import ProximityEngine
from .models import SignalSample


def parse_sample(value: str) -> SignalSample:
    cleaned = value.strip().casefold()
    if cleaned in {"missing", "none", "-"}:
        return SignalSample(None)
    return SignalSample(int(cleaned))


def main() -> None:
    engine = ProximityEngine()
    for line in sys.stdin:
        if line.strip().casefold() == "quit":
            break
        try:
            state = engine.update(parse_sample(line))
        except ValueError:
            sys.stdout.write("INVALID\n")
        else:
            sys.stdout.write(state.value + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
