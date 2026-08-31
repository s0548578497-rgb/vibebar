$ErrorActionPreference = "Stop"
$Repository = Split-Path -Parent $PSScriptRoot
& "$PSScriptRoot\setup.ps1"

$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "VibeBar.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $PSScriptRoot "start_vibebar.cmd"
$Shortcut.WorkingDirectory = $Repository
$Shortcut.Description = "VibeBar for Windows"
$Shortcut.Save()

Write-Output "VibeBar installed. Startup shortcut: $ShortcutPath"
