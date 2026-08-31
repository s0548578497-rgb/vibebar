$ErrorActionPreference = "Stop"
$Repository = Split-Path -Parent $PSScriptRoot
Push-Location $Repository
try {
    python -m vibebar_windows.app
}
finally {
    Pop-Location
}
