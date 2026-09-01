"""Socket for the existing whisper.cpp Turbo/Vulkan server in kodex."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType
import urllib.error
import urllib.request
import wave

import numpy as np

from vibebar_modular.wait import wait_until


@dataclass(frozen=True, slots=True)
class TurboPaths:
    workspace: Path
    server: Path
    model: Path
    vad_model: Path
    vulkan_bin: Path
    adapter: Path

    @classmethod
    def discover(cls, repository: Path) -> "TurboPaths":
        workspace = repository.parent
        whisper = workspace / "deps" / "whisper.cpp"
        return cls(
            workspace=workspace,
            server=whisper / "build-vulkan" / "bin" / "Release" / "whisper-server.exe",
            model=whisper / "models" / "ggml-large-v3-turbo-q5_0.bin",
            vad_model=workspace / "ggml-silero-v6.2.0.bin",
            vulkan_bin=workspace / "deps" / "VulkanSDK" / "Bin",
            adapter=workspace / "voice_agent" / "stt" / "turbo.py",
        )

    def validate(self) -> None:
        missing = [path for path in (self.server, self.model, self.vad_model, self.adapter) if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Turbo C++ component missing: {missing[0]}")


class CppTurboServer:
    url = "http://127.0.0.1:8091/"

    def __init__(self, paths: TurboPaths) -> None:
        self.paths = paths
        self.process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        if self._ready():
            return
        self.paths.validate()
        environment = os.environ.copy()
        environment["PATH"] = f"{self.paths.vulkan_bin}{os.pathsep}{environment.get('PATH', '')}"
        self.process = subprocess.Popen(
            self._command(),
            cwd=self.paths.workspace,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if not wait_until(self._ready, timeout=12):
            self.stop()
            raise TimeoutError("Turbo C++ server did not become ready")

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def _ready(self) -> bool:
        try:
            urllib.request.urlopen(self.url, timeout=0.25).close()
        except (urllib.error.URLError, TimeoutError):
            return False
        return True

    def _command(self) -> list[str]:
        return [
            str(self.paths.server), "-m", str(self.paths.model), "-l", "he",
            "-t", "8", "-bs", "2", "-ac", "0", "--vad",
            "-vm", str(self.paths.vad_model), "-vt", "0.35",
            "-vp", "120", "-vspd", "100", "--host", "127.0.0.1", "--port", "8091",
        ]


class CppTurboTranscriber:
    def __init__(self, repository: Path) -> None:
        self.paths = TurboPaths.discover(repository)
        self.server = CppTurboServer(self.paths)
        self.adapter = _load_adapter(self.paths.adapter)

    def transcribe(self, audio: np.ndarray) -> str:
        self.server.start()
        temporary = _temporary_wav_path()
        try:
            text, _elapsed = self.adapter.transcribe(
                audio,
                temporary,
                save_snapshot=_save_wav,
                url="http://127.0.0.1:8091/inference",
                beam=2,
            )
            return text
        finally:
            temporary.unlink(missing_ok=True)

    def close(self) -> None:
        self.server.stop()


def _load_adapter(path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location("vibebar_existing_turbo", path)
    if specification is None or specification.loader is None:
        raise ImportError(f"Cannot load existing Turbo adapter: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _temporary_wav_path() -> Path:
    descriptor, name = tempfile.mkstemp(prefix="vibebar-command-", suffix=".wav")
    os.close(descriptor)
    return Path(name)


def _save_wav(samples: np.ndarray, path: Path) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16_000)
        output.writeframes(np.asarray(samples, dtype=np.int16).tobytes())
