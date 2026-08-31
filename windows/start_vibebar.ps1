$ErrorActionPreference = "Stop"
$Repository = Split-Path -Parent $PSScriptRoot
$EnvironmentPython = Join-Path $Repository ".venv-windows\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $EnvironmentPython) { $EnvironmentPython } else { "python" }
Push-Location $Repository
try {
    & $Python -m vibebar_windows.app
}
finally {
    Pop-Location
}
