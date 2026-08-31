"""pbpaste-compatible Windows clipboard reader."""

from __future__ import annotations

import sys
import tkinter


def main() -> None:
    root = tkinter.Tk()
    root.withdraw()
    try:
        text = root.clipboard_get()
    except tkinter.TclError:
        text = ""
    finally:
        root.destroy()
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
