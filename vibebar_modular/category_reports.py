"""Shared replaceable, atomic category-section writer for generated reports."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Protocol


class CategoryReportWriter(Protocol):
    def enrich(self, report: Path, summary: str) -> None: ...


class NullCategoryReportWriter:
    def enrich(self, report: Path, summary: str) -> None:
        return None


class MarkdownCategoryReportWriter:
    MARK_START = "<!-- vibebar:categories:start -->"
    MARK_END = "<!-- vibebar:categories:end -->"

    def enrich(self, report: Path, summary: str) -> None:
        if not report.exists():
            return
        content = report.read_text(encoding="utf-8")
        block = f"{self.MARK_START}\n{summary}\n{self.MARK_END}"
        pattern = re.compile(re.escape(self.MARK_START) + r".*?" + re.escape(self.MARK_END), re.S)
        updated = pattern.sub(block, content) if pattern.search(content) else content.rstrip() + "\n\n" + block + "\n"
        temporary = report.with_suffix(report.suffix + ".categories")
        temporary.write_text(updated, encoding="utf-8")
        temporary.replace(report)
