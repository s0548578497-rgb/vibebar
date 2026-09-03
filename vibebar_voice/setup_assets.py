"""Install openWakeWord runtime assets and the configured Hey Computer model."""

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
    configured = os.environ.get("VIBEBAR_MODEL_DIR")
    local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    target = Path(configured) if configured else local / "VibeBar" / "models"
    target.mkdir(parents=True, exist_ok=True)
    # The package downloader supplies the shared mel and embedding models.
    # The wake phrase itself is installed separately and checksum-verified.
    # A non-official name makes openWakeWord fetch only its shared feature
    # models; downloading an empty list would pull every bundled wake phrase.
    openwakeword.utils.download_models(["hey_computer.onnx"], str(target))
    install_computer_model(target)


if __name__ == "__main__":
    main()
