"""Single macOS composition root."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from vibebar_modular.platform_contracts import AudioCue, GlobalHotkey, JournalChangeListener
from vibebar_modular.platform_nulls import NullJournalChangeListener
from vibebar_modular.command_language import CommandVocabulary, LocalizedEntrySocket
from vibebar_modular.custom_commands import CustomCommandRepository, CustomCommandStore
from vibebar_modular.runner import SubprocessRunner
from vibebar_modular.sockets import SocketSet, build_sockets

from .audio_cue import MacAudioCue
from .bluetooth import BluetoothConnectionSocket, NullBluetoothConnectionSocket, SystemProfilerBluetoothSocket
from .delegated_hotkey import SuperwhisperHotkey


@dataclass(frozen=True, slots=True)
class MacSocketSet:
    core: SocketSet
    audio_cue: AudioCue
    hotkey: GlobalHotkey
    journal_changes: JournalChangeListener
    bluetooth: BluetoothConnectionSocket
    commands: CustomCommandRepository


def assemble_macos(root: Path, device_name: str | None = None, allow_deletion: bool = False) -> MacSocketSet:
    runner = SubprocessRunner()
    core = build_sockets(root, allow_deletion=allow_deletion)
    commands = CustomCommandStore(root / "macos" / "custom_commands.json")
    words = CommandVocabulary.load(root / "resources" / "command_words.json")
    localized_entry = LocalizedEntrySocket(core.entry, words.merged(commands.aliases()))
    bluetooth: BluetoothConnectionSocket = (
        SystemProfilerBluetoothSocket(runner, device_name) if device_name else NullBluetoothConnectionSocket()
    )
    return MacSocketSet(
        core=replace(core, entry=localized_entry),
        audio_cue=MacAudioCue(runner),
        hotkey=SuperwhisperHotkey(),
        journal_changes=NullJournalChangeListener(),
        bluetooth=bluetooth,
        commands=commands,
    )
