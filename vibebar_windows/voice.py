"""Local Hey Jarvis wake word followed by local Whisper transcription."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Callable

import numpy as np

from .transcription import AudioTranscriber
from .audio_cue import AudioCue, NullAudioCue
from .diagnostics import DiagnosticLog, NullDiagnosticLog, text_fingerprint


@dataclass(frozen=True, slots=True)
class CaptureSettings:
    speech_level: float = 120.0
    start_timeout_blocks: int = 100
    trailing_silence_blocks: int = 20
    maximum_blocks: int = 375


class WakeWordSettings:
    def __init__(self, model: str, threshold: float) -> None:
        self.model = model
        self.threshold = threshold

    @classmethod
    def load(cls, path: Path) -> "WakeWordSettings":
        values = json.loads(path.read_text(encoding="utf-8"))
        return cls(str(values["model"]), float(values["threshold"]))


class VoiceController:
    def __init__(
        self,
        on_text: Callable[[str], None],
        on_status: Callable[[str], None],
        transcriber: AudioTranscriber,
        model_dir: Path | None = None,
        wakeword: WakeWordSettings | None = None,
        cue: AudioCue | None = None,
        diagnostics: DiagnosticLog | None = None,
        capture: CaptureSettings | None = None,
    ) -> None:
        self.on_text = on_text
        self.on_status = on_status
        self.transcriber = transcriber
        local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.model_dir = model_dir or local / "VibeBar" / "models"
        self.wakeword = wakeword or WakeWordSettings("hey_jarvis_v0.1.onnx", 0.5)
        self.cue = cue or NullAudioCue()
        self.diagnostics = diagnostics or NullDiagnosticLog()
        self.capture = capture or CaptureSettings()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.requested = False
        self.command_event = threading.Event()
        self.command_lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self.requested

    def toggle(self) -> bool:
        if self.enabled:
            self.stop()
        else:
            self.start()
        return self.enabled

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.requested = True
        self.diagnostics.event("voice_start")
        self.thread = threading.Thread(target=self._run, name="vibebar-voice", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.requested = False
        self.stop_event.set()
        self.diagnostics.event("voice_stop")

    def _run(self) -> None:
        try:
            self._listen_loop()
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            self.diagnostics.event("voice_failure", error=type(error).__name__)
            self.on_status(str(error))
        finally:
            self.requested = False
            self.thread = None

    def _listen_loop(self) -> None:
        import sounddevice as sd
        wake_model = self._wake_model()
        self.on_status("voice_listening")
        self.diagnostics.event("listener_ready")
        with sd.InputStream(samplerate=16_000, channels=1, dtype="int16", blocksize=1_280) as stream:
            while not self.stop_event.is_set():
                frame, _overflowed = stream.read(1_280)
                score = float(next(iter(wake_model.predict(frame[:, 0]).values())))
                if score >= self.wakeword.threshold or self.command_event.is_set():
                    self.diagnostics.event("command_triggered", score=round(score, 4))
                    self.command_event.clear()
                    wake_model.reset()
                    self._handle_command(stream)
                    self.on_status("voice_listening")

    def request_command(self) -> None:
        self.diagnostics.event("command_requested", listener=self.enabled)
        if self.enabled:
            self.command_event.set()
            return
        threading.Thread(target=self._one_shot, name="vibebar-command", daemon=True).start()

    def _one_shot(self) -> None:
        if not self.command_lock.acquire(blocking=False):
            return
        try:
            import sounddevice as sd
            with sd.InputStream(samplerate=16_000, channels=1, dtype="int16", blocksize=1_280) as stream:
                self._handle_command(stream, ignore_stop=True)
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            self.diagnostics.event("command_failure", error=type(error).__name__)
            self.on_status(str(error))
        finally:
            self.command_lock.release()

    def _handle_command(self, stream: object, ignore_stop: bool = False) -> None:
        self.diagnostics.event("cue_started")
        played = self.cue.play()
        self.diagnostics.event("cue_completed", queued=played)
        self.on_status("voice_command")
        self.diagnostics.event("capture_started")
        audio = self._capture_command(stream, ignore_stop)
        self.diagnostics.event("capture_completed", samples=int(audio.size))
        self.diagnostics.event("transcription_started")
        text = self.transcriber.transcribe(audio)
        self.diagnostics.event(
            "transcription_completed", characters=len(text), fingerprint=text_fingerprint(text)
        )
        if text:
            self.on_text(text)

    def _wake_model(self) -> object:
        from openwakeword.model import Model

        required = (
            self.wakeword.model,
            "melspectrogram.onnx",
            "embedding_model.onnx",
        )
        missing = [name for name in required if not (self.model_dir / name).exists()]
        if missing:
            raise FileNotFoundError("Wake-word models are missing; run windows/setup.ps1")
        return Model(
            wakeword_models=[str(self.model_dir / self.wakeword.model)],
            inference_framework="onnx",
            melspec_model_path=str(self.model_dir / required[1]),
            embedding_model_path=str(self.model_dir / required[2]),
        )

    def _capture_command(self, stream: object, ignore_stop: bool = False) -> np.ndarray:
        frames: list[np.ndarray] = []
        silent_blocks = 0
        speech_seen = False
        maximum_level = 0.0
        reason = "maximum_duration"
        for block_index in range(self.capture.maximum_blocks):
            if self.stop_event.is_set() and not ignore_stop:
                reason = "listener_stopped"
                break
            frame, _overflowed = stream.read(1_280)
            mono = np.asarray(frame[:, 0], dtype=np.int16)
            frames.append(mono)
            level = float(np.sqrt(np.mean(mono.astype(np.float32) ** 2)))
            maximum_level = max(maximum_level, level)
            if level >= self.capture.speech_level:
                speech_seen = True
                silent_blocks = 0
            elif speech_seen:
                silent_blocks += 1
            if speech_seen and silent_blocks >= self.capture.trailing_silence_blocks:
                reason = "silence_after_speech"
                break
            if not speech_seen and block_index + 1 >= self.capture.start_timeout_blocks:
                reason = "no_speech"
                break
        self.diagnostics.event(
            "capture_stopped", reason=reason, speech_seen=speech_seen, maximum_level=round(maximum_level, 1)
        )
        return np.concatenate(frames) if frames else np.array([], dtype=np.int16)

    def close(self) -> None:
        self.stop()
        self.transcriber.close()
