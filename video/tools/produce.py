from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import struct
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ.get("VIBEBAR_TTS_CONFIG", Path.home() / "Tamlul" / "config.json"))


def wav(pcm: bytes) -> bytes:
    rate, channels, bits = 24_000, 1, 16
    byte_rate = rate * channels * bits // 8
    align = channels * bits // 8
    header = struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ",
                         16, 1, channels, rate, byte_rate, align, bits, b"data", len(pcm))
    return header + pcm


def synthesize(text: str) -> bytes:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    settings = config["gemini_tts"]
    key = settings.get("api_key") or config["gemini"]["api_key"]
    prompt = "Прочитай по-русски естественно, тепло и уверенно, как спокойный автор технологического фильма. " + text
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {
        "responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {
            "prebuiltVoiceConfig": {"voiceName": settings["voice"]}}}}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings['model']}:generateContent?key={key}"
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read())
    encoded = payload["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    return wav(base64.b64decode(encoded))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    scenes = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    chosen = scenes if args.all else [scene for scene in scenes if scene["id"] == args.scene]
    if not chosen:
        raise SystemExit("choose --all or an existing --scene")
    (ROOT / "audio").mkdir(exist_ok=True)
    for scene in chosen:
        (ROOT / "audio" / f"{scene['id']}.wav").write_bytes(synthesize(scene["narration"]))


if __name__ == "__main__":
    main()
