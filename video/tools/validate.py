"""Validate expected presentation assets and inspect final media streams."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def probe(path: Path) -> dict[str, object]:
    completed = subprocess.run(
        ("ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,codec_name,width,height,sample_rate",
         "-of", "json", str(path)), check=True, capture_output=True, text=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    scenes = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    report: dict[str, object] = {"scenes": []}
    for scene in scenes:
        identifier = scene["id"]
        required = [ROOT / scene["visual"], ROOT / "audio" / f"{identifier}.wav",
                    ROOT / "segments" / f"{identifier}.mp4"]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"scene {identifier} is incomplete: {missing}")
        report["scenes"].append({"id": identifier, "video": probe(required[2])})
    final = ROOT / "vibebar-russian-demo.mp4"
    final_probe = probe(final)
    streams = final_probe["streams"]
    if {stream["codec_type"] for stream in streams} != {"video", "audio"}:
        raise RuntimeError("final movie must contain video and audio")
    video = next(stream for stream in streams if stream["codec_type"] == "video")
    if (video.get("width"), video.get("height")) != (1920, 1080):
        raise RuntimeError("final movie must be Full HD")
    report["final"] = final_probe
    (ROOT / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
