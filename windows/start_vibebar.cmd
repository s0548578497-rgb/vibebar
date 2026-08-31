@echo off
setlocal
cd /d "%~dp0\.."
if exist ".venv-windows\Scripts\python.exe" (
  ".venv-windows\Scripts\python.exe" -m vibebar_windows.app
) else (
  python -m vibebar_windows.app
)
