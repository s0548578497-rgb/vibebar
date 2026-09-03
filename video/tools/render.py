from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import wave


ROOT = Path(__file__).resolve().parents[1]


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as reader:
        return reader.getnframes() / reader.getframerate()


def stamp(seconds: float) -> str:
    minutes, remainder = divmod(seconds, 60)
    return f"0:{int(minutes):02d}:{remainder:05.2f}"


def caption_chunks(text: str, limit: int = 68) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        if current and len(" ".join((*current, word))) > limit:
            chunks.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks


def wrap_caption(text: str, width: int = 38) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if current and len(" ".join((*current, word))) > width:
            lines.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        lines.append(" ".join(current))
    return r"\N".join(lines)


def subtitle(scene: dict[str, str], seconds: float) -> Path:
    path = ROOT / "subtitles" / f"{scene['id']}.ass"
    path.parent.mkdir(exist_ok=True)
    end = stamp(seconds)
    content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Caption,Arial,42,&H00FFFFFF,&H000000FF,&H00102035,&H99000000,0,0,0,0,100,100,0,0,1,3,1,2,120,120,60,1
Style: Title,Arial,54,&H00FFFFFF,&H000000FF,&H00102035,&H77000000,1,0,0,0,100,100,0,0,1,3,1,8,100,100,55,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
""" + f"Dialogue: 0,0:00:00.00,{end},Title,,0,0,0,,{scene['title']}\n"
    chunks = caption_chunks(scene["narration"].replace("\n", " "))
    weight = sum(len(chunk) for chunk in chunks)
    cursor = 0.0
    for index, chunk in enumerate(chunks):
        finish = seconds if index == len(chunks) - 1 else cursor + seconds * len(chunk) / weight
        content += f"Dialogue: 0,{stamp(cursor)},{stamp(finish)},Caption,,0,0,0,,{wrap_caption(chunk)}\n"
        cursor = finish
    path.write_text(content, encoding="utf-8-sig")
    return path


def render_scene(scene: dict[str, str]) -> Path:
    audio = ROOT / "audio" / f"{scene['id']}.wav"
    visual = ROOT / scene["visual"]
    output = ROOT / "segments" / f"{scene['id']}.mp4"
    output.parent.mkdir(exist_ok=True)
    seconds = duration(audio)
    frames = max(1, round(seconds * 30))
    zoom = "min(zoom+0.00035,1.10)" if scene["motion"] == "in" else "if(eq(on,1),1.10,max(zoom-0.00035,1.0))"
    subtitle_path = subtitle(scene, seconds).relative_to(ROOT.parent).as_posix()
    vf = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
          "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1d36,"
          f"zoompan=z='{zoom}':d={frames}:s=1920x1080:fps=30,subtitles='{subtitle_path}'")
    subprocess.run(("ffmpeg", "-y", "-loop", "1", "-i", str(visual), "-i", str(audio),
                    "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)),
                   check=True, cwd=ROOT.parent)
    return output


def concatenate(outputs: list[Path]) -> None:
    listing = ROOT / "segments" / "concat.txt"
    listing.write_text("".join(f"file '{path.as_posix()}'\n" for path in outputs), encoding="utf-8")
    subprocess.run(("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(ROOT / "vibebar-russian-demo.mp4")), check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--concat", action="store_true")
    args = parser.parse_args()
    scenes = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if args.concat:
        concatenate([ROOT / "segments" / f"{scene['id']}.mp4" for scene in scenes])
        return
    chosen = scenes if args.all else [scene for scene in scenes if scene["id"] == args.scene]
    outputs = [render_scene(scene) for scene in chosen]
    if args.all:
        concatenate(outputs)


if __name__ == "__main__":
    main()
