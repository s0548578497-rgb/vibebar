"""Socket for the existing whisper.cpp Turbo/Vulkan server in kodex."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import json
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
    vulkan_bin: Path | None
    adapter: Path | None

    @classmethod
    def discover(cls, repository: Path) -> "TurboPaths":
        """Backward-compatible Windows discovery."""
        return cls.discover_windows(repository)

    @classmethod
    def discover_windows(cls, repository: Path) -> "TurboPaths":
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

    @classmethod
    def discover_macos(cls, repository: Path) -> "TurboPaths":
        workspace = repository
        whisper = repository / "macos" / "deps" / "whisper.cpp"
        return cls(
            workspace=workspace,
            server=whisper / "build" / "bin" / "whisper-server",
            model=whisper / "models" / "ggml-large-v3-turbo.bin",
            vad_model=whisper / "models" / "ggml-silero-v6.2.0.bin",
            vulkan_bin=None,
            adapter=None,
        )

    def validate(self) -> None:
        required = (self.server, self.model, self.vad_model)
        missing = [path for path in required if not path.exists()]
        if self.adapter is not None and not self.adapter.exists():
            missing.append(self.adapter)
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
        if self.paths.vulkan_bin is not None:
            environment["PATH"] = f"{self.paths.vulkan_bin}{os.pathsep}{environment.get('PATH', '')}"
        self.process = subprocess.Popen(
            self._command(),
            cwd=self.paths.workspace,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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
    def __init__(self, repository: Path, paths: TurboPaths | None = None) -> None:
        self.paths = paths or TurboPaths.discover_windows(repository)
        self.server = CppTurboServer(self.paths)
        self.adapter = _load_adapter(self.paths.adapter) if self.paths.adapter else ServerTranscriptionAdapter()

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


class ServerTranscriptionAdapter:
    def transcribe(
        self, audio: np.ndarray, path: Path, save_snapshot: Callable[[np.ndarray, Path], None], url: str, beam: int
    ) -> tuple[str, float]:
        save_snapshot(audio, path)
        boundary = "----VibeBarWhisperBoundary"
        content = path.read_bytes()
        body = _multipart(boundary, content, beam)
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return str(payload.get("text", "")).strip(), 0.0


def _multipart(boundary: str, content: bytes, beam: int) -> bytes:
    lines = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\njson\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"beam_size\"\r\n\r\n{beam}\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"command.wav\"\r\n",
        "Content-Type: audio/wav\r\n\r\n",
    ]
    prefix = "".join(lines).encode("utf-8")
    suffix = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return prefix + content + suffix


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
