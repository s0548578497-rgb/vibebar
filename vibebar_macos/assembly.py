"""Single macOS composition root."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from vibebar_modular.platform_contracts import AudioCue, JournalChangeListener
from vibebar_modular.platform_nulls import NullJournalChangeListener
from vibebar_modular.command_language import CommandVocabulary, LocalizedEntrySocket
from vibebar_modular.custom_commands import CustomCommandRepository, CustomCommandStore
from vibebar_modular.categories import CategoryService, JsonClassificationRepository, load_categories
from vibebar_modular.category_reports import CategoryReportWriter, MarkdownCategoryReportWriter
from vibebar_modular.compositions import Composition, get_composition
from vibebar_modular.language import LanguageController
from vibebar_modular.runner import SubprocessRunner
from vibebar_modular.sockets import SocketSet, build_sockets
from vibebar_voice.controller import WakeWordSettings
from vibebar_voice.cpp_whisper import CppTurboTranscriber, TurboPaths
from vibebar_voice.transcription import AudioTranscriber

from .audio_cue import MacAudioCue
from .bluetooth import BluetoothConnectionSocket, NullBluetoothConnectionSocket, SystemProfilerBluetoothSocket


@dataclass(frozen=True, slots=True)
class MacSocketSet:
    composition: Composition
    core: SocketSet
    audio_cue: AudioCue
    journal_changes: JournalChangeListener
    bluetooth: BluetoothConnectionSocket
    commands: CustomCommandRepository
    transcriber_factory: Callable[[], AudioTranscriber]
    wakeword: WakeWordSettings
    model_dir: Path
    categories: CategoryService
    category_reports: CategoryReportWriter
    language: LanguageController


def assemble_macos(root: Path, device_name: str | None = None, allow_deletion: bool = False) -> MacSocketSet:
    runner = SubprocessRunner()
    core = build_sockets(root, allow_deletion=allow_deletion)
    commands = CustomCommandStore(root / "macos" / "custom_commands.json")
    words = CommandVocabulary.load(root / "resources" / "command_words.json")
    localized_entry = LocalizedEntrySocket(core.entry, words.merged(commands.aliases()))
    categories = CategoryService(
        Path.home() / "vibebar-journal.md",
        load_categories(root / "resources" / "categories.json"),
        JsonClassificationRepository(root / "macos" / "classifications.json"),
        core.clock,
    )
    bluetooth: BluetoothConnectionSocket = (
        SystemProfilerBluetoothSocket(runner, device_name) if device_name else NullBluetoothConnectionSocket()
    )
    return MacSocketSet(
        composition=get_composition("macos"),
        core=replace(core, entry=localized_entry),
        audio_cue=MacAudioCue(runner),
        journal_changes=NullJournalChangeListener(),
        bluetooth=bluetooth,
        commands=commands,
        transcriber_factory=lambda: CppTurboTranscriber(root, TurboPaths.discover_macos(root)),
        wakeword=WakeWordSettings.load(root / "resources" / "wakeword.json"),
        model_dir=Path.home() / "Library" / "Application Support" / "VibeBar" / "models",
        categories=categories,
        category_reports=MarkdownCategoryReportWriter(),
        language=LanguageController(root / "resources" / "locales", root / "macos" / "settings.json"),
    )
