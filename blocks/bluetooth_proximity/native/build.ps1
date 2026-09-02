$ErrorActionPreference = "Stop"
$Compiler = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$Here = $PSScriptRoot
& $Compiler /nologo /target:exe /platform:x64 /out:"$Here\ClassicRssiReader.exe" "$Here\ClassicRssiReader.cs"
