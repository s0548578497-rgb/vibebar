# VibeBar on Windows

The Windows edition wraps the original VibeBar scripts through Git Bash. Task
classification, journal format, timing, reports, and clipboard-buffer behavior
remain the original implementation.

## Included

- live current-task timer;
- today's tasks, ideas, and reminders;
- the last clipboard entries with copy, delete, and clear actions;
- opt-in automatic clipboard monitoring;
- daily and weekly reports and journal opening;
- minimize-to-tray behavior;
- live language switching between Hebrew, Russian, and English.
- fully local `Hey Jarvis` wake word followed by the existing whisper.cpp
  Large-v3-Turbo/Vulkan engine from the parent `kodex` workspace.

Language catalogs are independent JSON files in `windows/locales`. Adding a
language requires one new catalog with the same keys; no UI code changes.

## Requirements and setup

- Windows 10 or newer;
- Python 3.11 or newer with Tkinter;
- Git for Windows, including Git Bash.

Run once from PowerShell:

```powershell
.\windows\setup.ps1
```

Start the application:

```powershell
.\windows\start_vibebar.ps1
```

`start_vibebar.cmd` can also be opened directly. To start VibeBar automatically
after signing in, run `windows/install.ps1`. `windows/uninstall.ps1` removes only
the startup shortcut and deliberately keeps all user data.

## Data

- Journal: `%USERPROFILE%\vibebar-journal.md`
- Clipboard history: `clipboard.txt` in this repository
- Digests: `digests` in this repository
- UI preference: `windows/settings.json`

Clipboard monitoring is off by default because copied text can contain secrets.
Deletion is connected only in the explicit Windows composition. The application
does not send journal or clipboard content over the network.

Voice listening is also off by default. When enabled, openWakeWord continuously
checks the microphone locally for `Hey Jarvis`. Only after detection is a command
captured and transcribed by the local C++ Turbo server on `127.0.0.1`. The C++
CLI requires a temporary WAV; it is deleted immediately after transcription and
is never sent outside the computer.
