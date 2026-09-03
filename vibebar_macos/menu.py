"""Localized SwiftBar presentation with every connected macOS capability."""

from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
import os
import re
import sys
from collections.abc import Callable

from .assembly import MacSocketSet, assemble_macos
from .voice_backend import VoiceBackendStore
from vibebar_modular.task_timer import JournalTaskTimerSocket


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.stdout.buffer.write((render(root, assemble_macos(root)) + "\n").encode("utf-8"))


def render(root: Path, sockets: MacSocketSet) -> str:
    t = sockets.language.catalog.text
    command = f"{root / '.venv-macos' / 'bin' / 'python'} -m vibebar_macos.menu_actions"
    journal = _journal_path()
    sections = _journal_sections(journal)
    voice = VoiceBackendStore(root / "macos" / "voice.json").load()
    timer = JournalTaskTimerSocket(journal, sockets.core.clock).load().display(sockets.core.clock.now())
    lines = [f"▶ {timer}", "---", _action(t("submit"), command, "add")]
    for key in ("tasks", "breaks", "ideas", "todos"):
        lines += _section(t(key), sections[key], key)
    lines += _clipboard(root, t, command)
    lines += ["---", t("reports") + " | size=10"]
    lines += [_action(t("daily_digest"), command, "daily"), _action(t("rebuild_digest"), command, "rebuild")]
    lines += [_action(t("weekly_digest"), command, "weekly"), _action(t("publish_digest"), command, "publish")]
    lines += ["---", _action(t("categories"), command, "category")]
    lines += [_action(t("add_command"), command, "command-add"), _action(t("delete"), command, "command-delete")]
    lines += [_action(voice.label(sockets.language.catalog.code), command, "voice-backend")]
    lines += [_action(t("language"), command, "language"), _action(t("edit_journal"), command, "journal")]
    return "\n".join(lines)


def _journal_path() -> Path:
    return Path(os.environ.get("VIBEBAR_FILE", str(Path.home() / "vibebar-journal.md")))


def _journal_sections(path: Path) -> dict[str, list[tuple[str, str]]]:
    rows = {key: [] for key in ("tasks", "breaks", "ideas", "todos")}
    if not path.exists():
        return rows
    current = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line == f"## {date.today().isoformat()}"
            continue
        match = re.match(r"^-\s*(\d{1,2}:\d{2})\s*[·•]\s*(.*)$", line)
        if current and match:
            kind, text = _kind(match.group(2).strip())
            rows[kind].append((match.group(1), text))
    return rows


def _kind(text: str) -> tuple[str, str]:
    text = re.sub(r"\s*<!--.*?-->\s*$", "", text)
    for marker, kind in (("💡", "ideas"), ("❗", "todos"), ("⏸", "breaks")):
        if text.startswith(marker):
            return kind, text[len(marker):].strip()
    return "tasks", text


def _section(title: str, rows: list[tuple[str, str]], key: str) -> list[str]:
    lines = ["---", f"{title} ({len(rows)}) | size=10 vibebar_section={key}"]
    lines.extend(f"{time}  {_safe(text)} | font=Menlo size=12" for time, text in reversed(rows[-7:]))
    return lines


def _clipboard(root: Path, translate: Callable[[str], str], command: str) -> list[str]:
    path = Path(os.environ.get("VIBEBAR_BUFFER", str(root / "clipboard.txt")))
    rows: list[tuple[int, str]] = []
    if path.exists():
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                rows.append((index, base64.b64decode(line).decode("utf-8", "replace")))
            except ValueError:
                continue
    lines = ["---", f"{translate('clipboard')} ({len(rows)}) | size=10 vibebar_section=clipboard"]
    lines.append(_action(translate("capture_clipboard"), command, "clipboard-add"))
    for index, value in reversed(rows[-10:]):
        lines.append(_action(f"{index}  {_safe(value, 42)}", command, "clipboard-copy", str(index)))
        lines.append("--" + _action(translate("open"), command, "clipboard-show", str(index)))
        lines.append("--" + _action(translate("delete"), command, "clipboard-delete", str(index)))
    lines.append(_action(translate("clear"), command, "clipboard-clear"))
    return lines


def _action(label: str, command: str, action: str, value: str | None = None) -> str:
    python, module = command.split(" -m ", 1)
    extra = f" param4={value}" if value is not None else ""
    return f"{label} | bash={python} param1=-m param2={module} param3={action}{extra} terminal=false refresh=true"


def _safe(value: str, limit: int = 60) -> str:
    one = " ".join(value.replace("|", "¦").split())
    return one if len(one) <= limit else one[: limit - 1] + "…"


if __name__ == "__main__":
    main()
