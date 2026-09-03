# Modular Russian demo video

The finished Russian presentation is [vibebar-russian-demo.mp4](vibebar-russian-demo.mp4).
The complete feature comparison and attribution are in
[description-ru.md](description-ru.md).

Every scene is independent. Edit `manifest.json`, then regenerate only that scene:

```powershell
.\.venv-windows\Scripts\python.exe video\tools\produce.py --scene 03
```

Render or concatenate without regenerating narration:

```powershell
.\.venv-windows\Scripts\python.exe video\tools\render.py --scene 03
.\.venv-windows\Scripts\python.exe video\tools\render.py --all
```

The narration provider reads its configuration from
`%USERPROFILE%\Tamlul\config.json` by default. Set `VIBEBAR_TTS_CONFIG` to use
another location. The key is read only at runtime and is never copied into this
repository.

Generated audio, subtitles, scene renders, previews and validation reports are
deliberately excluded from Git. They can be reproduced from the manifest. The
finished presentation is committed as the reviewable artifact.
