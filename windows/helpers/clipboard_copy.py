"""pbcopy-compatible Windows clipboard writer."""

from __future__ import annotations

import sys
import tkinter


def main() -> None:
    text = sys.stdin.read()
    root = tkinter.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()


if __name__ == "__main__":
    main()
