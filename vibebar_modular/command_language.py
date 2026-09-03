"""Language-neutral command routing in front of the unchanged journal socket."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .contracts import CommandResult, EntrySocket


@dataclass(frozen=True, slots=True)
class CommandVocabulary:
    aliases: dict[str, tuple[str, ...]]

    @classmethod
    def load(cls, path: Path) -> "CommandVocabulary":
        raw = json.loads(path.read_text(encoding="utf-8"))
        aliases = {kind: tuple(alias.casefold() for alias in values) for kind, values in raw.items()}
        return cls(aliases)

    def classify(self, text: str) -> tuple[str, str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        folded = cleaned.casefold()
        for kind, aliases in self.aliases.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if folded == alias or folded.startswith(alias + " "):
                    body = cleaned[len(alias):].lstrip(" ,.:;!?—-")
                    return kind, cleaned if kind == "task" else body
        return "task", cleaned

    def merged(self, additions: dict[str, tuple[str, ...]]) -> "CommandVocabulary":
        values = {kind: list(words) for kind, words in self.aliases.items()}
        for kind, words in additions.items():
            values.setdefault(kind, []).extend(word.casefold() for word in words)
        return CommandVocabulary({kind: tuple(words) for kind, words in values.items()})


@dataclass(frozen=True, slots=True)
class LocalizedEntrySocket:
    inner: EntrySocket
    vocabulary: CommandVocabulary

    def submit(self, text: str) -> CommandResult:
        kind, body = self.vocabulary.classify(text)
        if kind == "idea":
            normalized = f"идея {body}" if body else "идея"
        elif kind == "todo":
            normalized = f"не забыть {body}" if body else "не забыть"
        elif kind == "pause":
            normalized = "перерыв"
        else:
            normalized = body
        return self.inner.submit(normalized)
