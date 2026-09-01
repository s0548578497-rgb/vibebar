$ErrorActionPreference = "Stop"
$Repository = Split-Path -Parent $PSScriptRoot
$EnvironmentPython = Join-Path $Repository ".venv-windows\Scripts\pythonw.exe"
$Python = if (Test-Path -LiteralPath $EnvironmentPython) { $EnvironmentPython } else { "pythonw" }
Push-Location $Repository
try {
    Start-Process -FilePath $Python -ArgumentList "-m", "vibebar_windows.app" -WorkingDirectory $Repository
}
finally {
    Pop-Location
}
