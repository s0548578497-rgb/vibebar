"""Open a file with its registered Windows application."""

from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(2)
    os.startfile(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
