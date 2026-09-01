"""Install shared openWakeWord assets and the configured community model."""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
import urllib.request

import openwakeword


COMPUTER_URL = "https://huggingface.co/Soulcreek2/speechkit-wakeword-models/resolve/main/hey_computer.onnx"
COMPUTER_SHA256 = "3acbd9ffff04beba2d16ebdfd0d4c734d65fecdd22446f25f4d0afa6e5d7606b"


def install_computer_model(target: Path) -> None:
    destination = target / "hey_computer.onnx"
    if destination.exists() and _sha256(destination) == COMPUTER_SHA256:
        return
    temporary = destination.with_suffix(".onnx.download")
    try:
        urllib.request.urlretrieve(COMPUTER_URL, temporary)
        if _sha256(temporary) != COMPUTER_SHA256:
            raise RuntimeError("Hey Computer model checksum mismatch")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    target = local / "VibeBar" / "models"
    target.mkdir(parents=True, exist_ok=True)
    openwakeword.utils.download_models(["hey_jarvis_v0.1"], str(target))
    install_computer_model(target)


if __name__ == "__main__":
    main()
