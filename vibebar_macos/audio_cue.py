from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vibebar_modular.contracts import CommandRunner


@dataclass(frozen=True, slots=True)
class MacAudioCue:
    runner: CommandRunner
    sound: Path = Path("/System/Library/Sounds/Pop.aiff")

    def play(self) -> bool:
        return self.runner.run(("afplay", str(self.sound))).succeeded
