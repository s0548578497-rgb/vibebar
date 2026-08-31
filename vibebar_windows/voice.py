"""Local Hey Jarvis wake word followed by local Whisper transcription."""

from __future__ import annotations

import os
from pathlib import Path
import threading
from typing import Callable
import winsound

import numpy as np


class VoiceController:
    def __init__(
        self,
        on_text: Callable[[str], None],
        on_status: Callable[[str], None],
        model_dir: Path | None = None,
    ) -> None:
        self.on_text = on_text
        self.on_status = on_status
        local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.model_dir = model_dir or local / "VibeBar" / "models"
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.requested = False

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
        self.thread = threading.Thread(target=self._run, name="vibebar-voice", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.requested = False
        self.stop_event.set()

    def _run(self) -> None:
        try:
            self._listen_loop()
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            self.on_status(str(error))
        finally:
            self.requested = False
            self.thread = None

    def _listen_loop(self) -> None:
        import sounddevice as sd
        from faster_whisper import WhisperModel

        wake_model = self._wake_model()
        whisper = WhisperModel(
            "Systran/faster-whisper-small",
            device="cpu",
            compute_type="int8",
            local_files_only=True,
        )
        self.on_status("voice_listening")
        with sd.InputStream(samplerate=16_000, channels=1, dtype="int16", blocksize=1_280) as stream:
            while not self.stop_event.is_set():
                frame, _overflowed = stream.read(1_280)
                score = float(next(iter(wake_model.predict(frame[:, 0]).values())))
                if score >= 0.5:
                    wake_model.reset()
                    winsound.Beep(880, 120)
                    self.on_status("voice_command")
                    audio = self._capture_command(stream)
                    text = self._transcribe(whisper, audio)
                    if text:
                        self.on_text(text)
                    self.on_status("voice_listening")

    def _wake_model(self) -> object:
        from openwakeword.model import Model

        required = (
            "hey_jarvis_v0.1.onnx",
            "melspectrogram.onnx",
            "embedding_model.onnx",
        )
        missing = [name for name in required if not (self.model_dir / name).exists()]
        if missing:
            raise FileNotFoundError("Wake-word models are missing; run windows/setup.ps1")
        return Model(
            wakeword_models=[str(self.model_dir / required[0])],
            inference_framework="onnx",
            melspec_model_path=str(self.model_dir / required[1]),
            embedding_model_path=str(self.model_dir / required[2]),
        )

    def _capture_command(self, stream: object) -> np.ndarray:
        frames: list[np.ndarray] = []
        silent_blocks = 0
        for block_index in range(250):
            if self.stop_event.is_set():
                break
            frame, _overflowed = stream.read(1_280)
            mono = np.asarray(frame[:, 0], dtype=np.int16)
            frames.append(mono)
            level = float(np.sqrt(np.mean(mono.astype(np.float32) ** 2)))
            silent_blocks = silent_blocks + 1 if level < 300 else 0
            if block_index >= 8 and silent_blocks >= 15:
                break
        return np.concatenate(frames) if frames else np.array([], dtype=np.int16)

    @staticmethod
    def _transcribe(model: object, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        samples = audio.astype(np.float32) / 32768.0
        segments, _info = model.transcribe(samples, beam_size=3, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
