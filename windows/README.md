# VibeBar on Windows

The Windows adapter runs the original VibeBar scripts through Git Bash. It does
not duplicate classification, journal, clipboard-buffer, or digest logic.

## Requirements

- Windows 10 or newer
- Python 3.11 or newer with Tkinter
- Git for Windows, including Git Bash

## Start

From PowerShell:

```powershell
.\windows\start_vibebar.ps1
```

The window can submit an activity, capture the current clipboard item, and open
the daily digest. Data remains in the same plain-text formats as macOS.

Default files:

- Journal: `%USERPROFILE%\vibebar-journal.md`
- Clipboard history: `clipboard.txt` in this repository
- Digests: `digests` in this repository

Automatic paste is disabled on Windows by default. Deletion also remains sealed
unless a composition explicitly enables the real recycle-bin socket.
