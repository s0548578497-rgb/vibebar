@echo off
setlocal
cd /d "%~dp0\.."
if exist ".venv-windows\Scripts\python.exe" (
  start "" ".venv-windows\Scripts\pythonw.exe" -m vibebar_windows.app
  start "" /b ".venv-windows\Scripts\pythonw.exe" -m absence_break.live
) else (
  start "" pythonw -m vibebar_windows.app
  start "" /b pythonw -m absence_break.live
)
