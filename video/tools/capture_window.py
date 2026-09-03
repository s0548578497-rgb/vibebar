"""Capture one named window without exposing the rest of the desktop."""

from __future__ import annotations

import ctypes
import argparse
from pathlib import Path

from PIL import ImageGrab


def find_window(fragment: str) -> int:
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def visit(handle: int, _parameter: int) -> bool:
        length = ctypes.windll.user32.GetWindowTextLengthW(handle)
        title = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(handle, title, length + 1)
        if fragment.casefold() in title.value.casefold() and ctypes.windll.user32.IsWindowVisible(handle):
            matches.append(handle)
        return True

    ctypes.windll.user32.EnumWindows(callback_type(visit), 0)
    if not matches:
        raise RuntimeError(f"window not found: {fragment}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="VibeBar")
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "assets" / "windows-ui.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    ImageGrab.grab(window=find_window(args.title)).save(output)


if __name__ == "__main__":
    main()
