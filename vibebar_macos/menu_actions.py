"""Commands exposed by the native SwiftBar presentation adapter."""

from __future__ import annotations

import argparse
from pathlib import Path
import os
import subprocess

from .assembly import MacSocketSet, assemble_macos
from .dialogs import ask, choose
from .voice_state import VoiceState


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sockets = assemble_macos(root, allow_deletion=True)
    _dispatch(root, sockets, args.action, args.value)
    sockets.core.menu.refresh()


def _dispatch(root: Path, sockets: MacSocketSet, action: str, value: str | None) -> None:
    if action == "add":
        text = ask(sockets.language.catalog.text("input_prompt"))
        if text:
            sockets.core.entry.submit(text)
    elif action == "language":
        sockets.language.switch()
    elif action == "voice":
        VoiceState(root / "macos" / "voice.json").toggle()
        _restart_voice()
    elif action == "daily":
        _digest(sockets, days=1, rebuild=False)
    elif action == "rebuild":
        _digest(sockets, days=1, rebuild=True)
    elif action == "weekly":
        _digest(sockets, days=7, rebuild=False)
    elif action == "publish":
        sockets.core.digest.publish_day()
    elif action == "journal":
        journal = Path(os.environ.get("VIBEBAR_FILE", str(Path.home() / "vibebar-journal.md")))
        sockets.core.opener.open(journal)
    elif action == "clipboard-add":
        sockets.core.clipboard.add_current()
    elif action == "clipboard-copy" and value:
        sockets.core.clipboard.copy(int(value))
    elif action == "clipboard-show" and value:
        sockets.core.clipboard.show(int(value))
    elif action == "clipboard-delete" and value:
        sockets.core.recycle_bin.delete_clipboard_item(int(value))
    elif action == "clipboard-clear":
        confirmed = choose(sockets.language.catalog.text("confirm_clear"), (sockets.language.catalog.text("clear"),))
        if confirmed:
            sockets.core.recycle_bin.clear_clipboard()
    elif action == "command-add":
        _add_command(sockets)
        _restart_voice()
    elif action == "command-delete":
        _delete_command(sockets)
        _restart_voice()
    elif action == "category":
        _assign_category(sockets)


def _digest(sockets: MacSocketSet, days: int, rebuild: bool) -> None:
    result = sockets.core.digest.build_week() if days == 7 else sockets.core.digest.build_day(rebuild)
    if result.succeeded and result.stdout.strip():
        report = Path(result.stdout.strip().splitlines()[-1])
        sockets.category_reports.enrich(report, sockets.categories.summary(days, sockets.language.catalog.code))
        sockets.core.opener.open(report)


def _add_command(sockets: MacSocketSet) -> None:
    phrase = ask(sockets.language.catalog.text("command_phrase"))
    kind = choose(sockets.language.catalog.text("command_kind"), ("task", "idea", "todo", "pause"))
    if phrase and kind:
        sockets.commands.add(phrase, kind)


def _delete_command(sockets: MacSocketSet) -> None:
    rows = sockets.commands.load()
    selected = choose(sockets.language.catalog.text("delete"), tuple(row.phrase for row in rows))
    if selected:
        sockets.commands.delete(selected)


def _assign_category(sockets: MacSocketSet) -> None:
    tasks = sockets.categories.tasks()
    labels = tuple(f"{task.time}  {task.text}" for task in tasks)
    selected = choose(sockets.language.catalog.text("categories"), labels)
    if not selected:
        return
    task = tasks[labels.index(selected)]
    categories = tuple(item.label(sockets.language.catalog.code) for item in sockets.categories.catalog)
    category = choose(sockets.language.catalog.text("assign_category"), categories)
    if category:
        sockets.categories.assign(task.key, int(category.split(" ", 1)[0]))


def _restart_voice() -> None:
    label = f"gui/{subprocess.run(('id', '-u'), capture_output=True, text=True, check=False).stdout.strip()}/com.vibebar.localvoice"
    subprocess.run(("launchctl", "kickstart", "-k", label), check=False)


if __name__ == "__main__":
    main()
