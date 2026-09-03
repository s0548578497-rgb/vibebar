"""Native macOS dialog boundary used by SwiftBar commands."""

from __future__ import annotations

import subprocess


def ask(prompt: str, title: str = "VibeBar") -> str | None:
    script = 'text returned of (display dialog %s default answer "" with title %s)' % (_quoted(prompt), _quoted(title))
    return _run(script)


def choose(prompt: str, values: tuple[str, ...], title: str = "VibeBar") -> str | None:
    if not values:
        return None
    choices = "{" + ",".join(_quoted(value) for value in values) + "}"
    script = 'item 1 of (choose from list %s with prompt %s with title %s)' % (
        choices, _quoted(prompt), _quoted(title)
    )
    return _run(script)


def _run(script: str) -> str | None:
    result = subprocess.run(("osascript", "-e", script), capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
