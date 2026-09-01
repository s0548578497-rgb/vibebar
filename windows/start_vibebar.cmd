@echo off
setlocal
cd /d "%~dp0\.."
if exist ".venv-windows\Scripts\python.exe" (
  start "" ".venv-windows\Scripts\pythonw.exe" -m vibebar_windows.app
) else (
  start "" pythonw -m vibebar_windows.app
)
