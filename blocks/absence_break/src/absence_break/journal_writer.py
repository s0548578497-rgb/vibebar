from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from .models import BreakEvent, BreakEventKind


class MarkdownJournalBreakWriter:
    def __init__(self, journal: Path) -> None:
        self.journal = journal

    def write(self, event: BreakEvent) -> None:
        marker = self._marker(event)
        content = self.journal.read_text(encoding="utf-8") if self.journal.exists() else ""
        if marker in content:
            return
        if event.kind is BreakEventKind.STARTED:
            text = f"⏸ הפסקה אוטומטית {marker}"
        else:
            task = self._last_task(content, event.occurred_at)
            if task is None:
                return
            text = f"{task} {marker}"
        self._insert(event.occurred_at, text, content)

    @staticmethod
    def _marker(event: BreakEvent) -> str:
        return f"<!-- proximity:{event.kind.value.lower()}:{event.occurred_at.isoformat()} -->"

    @staticmethod
    def _last_task(content: str, before: datetime) -> str | None:
        day = ""
        result: str | None = None
        for line in content.splitlines():
            if line.startswith("## "):
                day = line[3:].strip()
                continue
            match = re.match(r"^- (\d{2}:\d{2}) · (.*)$", line)
            if match is None or not day:
                continue
            try:
                stamp = datetime.fromisoformat(f"{day}T{match.group(1)}")
            except ValueError:
                continue
            text = match.group(2)
            if stamp <= before and not text.startswith(("⏸", "💡", "❗")):
                result = re.sub(r"\s*<!--.*?-->\s*$", "", text)
        return result

    def _insert(self, stamp: datetime, text: str, content: str) -> None:
        lines = content.splitlines()
        header = f"## {stamp:%Y-%m-%d}"
        entry = f"- {stamp:%H:%M} · {text}"
        if header not in lines:
            lines.extend(([""] if lines else []) + [header, entry])
        else:
            position = lines.index(header) + 1
            while position < len(lines) and not lines[position].startswith("## "):
                position += 1
            lines.insert(position, entry)
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.journal.with_suffix(self.journal.suffix + ".break")
        temporary.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        temporary.replace(self.journal)
