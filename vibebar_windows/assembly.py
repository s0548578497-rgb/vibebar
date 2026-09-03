"""Windows composition root; all business operations still use Legacy adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vibebar_modular.contracts import Clock, EntrySocket
from vibebar_modular.clock import SystemClock
from vibebar_modular.legacy import LegacyClipboardSocket, LegacyDigestSocket, LegacyEntrySocket, LegacyRecycleBin
from vibebar_modular.nulls import NullRecycleBin
from vibebar_modular.sockets import SocketSet

from .menu import WindowsMenuSocket
from .files import WindowsFileOpenerSocket
from .paths import discover
from .runner import WindowsBashRunner
from .command_language import CommandVocabulary, LocalizedEntrySocket
from .custom_commands import CustomCommandRepository, CustomCommandStore
from .cpp_whisper import CppTurboTranscriber
from .transcription import AudioTranscriber
from .view_model import LegacyMenuViewSocket, MenuViewSocket
from .hotkey import GlobalHotkey, WindowsGlobalHotkey
from .voice import WakeWordSettings
from .task_timer import JournalTaskTimerSocket, TaskTimerSocket
from .categories import CategoryService, JsonClassificationRepository, load_categories
from .category_reports import CategoryReportWriter, MarkdownCategoryReportWriter
from .digests import WindowsDigestSocket
from .audio_cue import AudioCue, WindowsWaveCue
from .diagnostics import DiagnosticLog, JsonLineDiagnosticLog
from .break_view import CombinedMenuViewSocket, JournalBreakViewSocket
from typing import Callable


@dataclass(frozen=True, slots=True)
class CommandSocketSet:
    entry: EntrySocket
    repository: CustomCommandRepository


@dataclass(frozen=True, slots=True)
class CategorySocketSet:
    service: CategoryService
    reports: CategoryReportWriter


def assemble_commands(repository: Path, inner: EntrySocket) -> CommandSocketSet:
    store = CustomCommandStore(repository / "windows" / "custom_commands.json")
    return CommandSocketSet(_localized_entry(repository, inner, store), store)


def assemble_transcriber(repository: Path) -> AudioTranscriber:
    return CppTurboTranscriber(repository)


def assemble_wakeword(repository: Path) -> WakeWordSettings:
    return WakeWordSettings.load(repository / "windows" / "wakeword.json")


def assemble_audio_cue() -> AudioCue:
    return WindowsWaveCue()


def assemble_diagnostics(repository: Path, clock: Clock) -> DiagnosticLog:
    return JsonLineDiagnosticLog(repository / "windows" / "diagnostics.jsonl", clock)


def assemble_task_timer(journal: Path, clock: Clock) -> TaskTimerSocket:
    return JournalTaskTimerSocket(journal, clock)


def assemble_categories(repository: Path, journal: Path, clock: Clock) -> CategorySocketSet:
    catalog = load_categories(repository / "windows" / "categories.json")
    store = JsonClassificationRepository(repository / "windows" / "classifications.json")
    return CategorySocketSet(CategoryService(journal, catalog, store, clock), MarkdownCategoryReportWriter())


def assemble_menu_view(repository: Path, environment: dict[str, str], clock: Clock) -> MenuViewSocket:
    runner = WindowsBashRunner(discover(repository), environment)
    legacy = LegacyMenuViewSocket(repository, runner)
    breaks = JournalBreakViewSocket(Path(environment["VIBEBAR_FILE"]), clock)
    return CombinedMenuViewSocket(legacy, breaks)


def assemble_hotkey(callback: Callable[[], None], on_error: Callable[[str], None]) -> GlobalHotkey:
    return WindowsGlobalHotkey(callback, on_error)


def rebuild_command_entry(repository: Path, inner: EntrySocket, store: CustomCommandRepository) -> EntrySocket:
    return _localized_entry(repository, inner, store)


def _localized_entry(repository: Path, inner: EntrySocket, store: CustomCommandRepository) -> EntrySocket:
    base = CommandVocabulary.load(repository / "resources" / "command_words.json")
    return LocalizedEntrySocket(inner, base.merged(store.aliases()))


def assemble_windows(
    repository: Path,
    environment: dict[str, str] | None = None,
    allow_deletion: bool = False,
) -> SocketSet:
    configured = default_environment(repository)
    if environment is not None:
        configured.update(environment)
    runner = WindowsBashRunner(discover(repository), configured)
    recycle_bin = LegacyRecycleBin(repository, runner) if allow_deletion else NullRecycleBin()
    legacy_digest = LegacyDigestSocket(repository, runner)
    clock = SystemClock()
    return SocketSet(
        entry=LegacyEntrySocket(repository, runner),
        clipboard=LegacyClipboardSocket(repository, runner),
        recycle_bin=recycle_bin,
        digest=WindowsDigestSocket(
            repository,
            Path(configured["VIBEBAR_DIGEST_DIR"]),
            Path(configured["VIBEBAR_FILE"]),
            runner,
            legacy_digest,
            clock,
        ),
        menu=WindowsMenuSocket(),
        opener=WindowsFileOpenerSocket(),
        clock=clock,
    )


def default_environment(repository: Path) -> dict[str, str]:
    return {
        "VIBEBAR_FILE": str(Path.home() / "vibebar-journal.md"),
        "VIBEBAR_BUFFER": str(repository / "clipboard.txt"),
        "VIBEBAR_DIGEST_DIR": str(repository / "digests"),
        "VIBEBAR_AUTOPASTE": "0",
    }
