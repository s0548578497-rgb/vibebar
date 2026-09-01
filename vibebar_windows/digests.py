"""Windows digest adapter: keep generation local and publishing explicit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from vibebar_modular.contracts import Clock, CommandResult, CommandRunner, DigestSocket


@dataclass(frozen=True, slots=True)
class WindowsDigestSocket:
    root: Path
    digest_dir: Path
    journal: Path
    runner: CommandRunner
    publisher: DigestSocket
    clock: Clock

    def build_day(self, rebuild: bool = False) -> CommandResult:
        arguments = [str(self.root / "bin" / "vibebar-day.sh"), "--no-open"]
        if rebuild:
            arguments.append("--rebuild")
        result = self.runner.run(arguments)
        destination = self.digest_dir / f"{self.clock.now().date().isoformat()}.md"
        return self._with_path(result, destination)

    def build_week(self, end: date | None = None) -> CommandResult:
        last_day = end or self.clock.now().date()
        result = self.runner.run(
            (str(self.root / "bin" / "vibebar-week.py"), str(self.journal), last_day.isoformat())
        )
        if not result.succeeded:
            return result
        destination = self.digest_dir / f"week-{last_day.isoformat()}.md"
        try:
            self._write_atomic(destination, result.stdout)
        except OSError as error:
            return CommandResult(1, stderr=str(error))
        return CommandResult(0, str(destination))

    def publish_day(self, day: date | None = None) -> CommandResult:
        return self.publisher.publish_day(day)

    @staticmethod
    def _with_path(result: CommandResult, path: Path) -> CommandResult:
        if not result.succeeded:
            return result
        return CommandResult(0, str(path), result.stderr)

    @staticmethod
    def _write_atomic(destination: Path, content: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination)
