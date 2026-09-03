$ErrorActionPreference = "Stop"
$Repository = Split-Path -Parent $PSScriptRoot
$Environment = Join-Path $Repository ".venv-windows"
if (-not (Test-Path -LiteralPath $Environment)) {
    python -m venv $Environment
}
& "$Environment\Scripts\python.exe" -m pip install -r "$PSScriptRoot\requirements.txt"
& "$Environment\Scripts\python.exe" -m pip install --no-build-isolation -e "$Repository\blocks\bluetooth_proximity"
& "$Environment\Scripts\python.exe" -m pip install --no-build-isolation -e "$Repository\blocks\absence_break"
Push-Location $Repository
try {
    & "$Environment\Scripts\python.exe" -m vibebar_windows.voice_setup
}
finally {
    Pop-Location
}
