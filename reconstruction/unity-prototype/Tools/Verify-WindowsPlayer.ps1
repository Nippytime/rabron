# Launch the actual compiled Windows player, not the Unity Editor.
# A fresh runtime marker, clean process exit and bounded deadline are required.
[CmdletBinding()]
param(
    [string]$ExePath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
        'Builds\RabronPrototype.exe'),
    [string]$LogPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
        'Logs\windows-player-smoke.log'),
    [ValidateRange(1, 300)]
    [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$LogPath = [System.IO.Path]::GetFullPath($LogPath)
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($LogPath)) |
    Out-Null

# Reject stale green logs even if the player cannot start.
if (Test-Path -LiteralPath $LogPath) {
    Remove-Item -LiteralPath $LogPath -Force
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'Windows Player startup evidence requires Windows.'
}
if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    throw "Fresh Windows Player executable missing: $ExePath"
}
$ExePath = (Resolve-Path -LiteralPath $ExePath).Path

$arguments = @(
    '-batchmode', '-nographics', '-rabronPlayerSmoke',
    '-logFile', ('"' + $LogPath + '"')
)
Write-Host "Launching real Windows Player startup smoke: $ExePath"
$process = Start-Process -FilePath $ExePath -ArgumentList $arguments `
    -WorkingDirectory ([System.IO.Path]::GetDirectoryName($ExePath)) -PassThru
try {
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        try { $process.Kill() } catch { }
        throw "Windows Player startup exceeded $TimeoutSeconds seconds."
    }
    $exitCode = $process.ExitCode
}
finally {
    $process.Dispose()
}

if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf) -or
    (Get-Item -LiteralPath $LogPath).Length -le 0) {
    throw "Windows Player did not produce fresh nonempty startup log: $LogPath"
}
$logText = Get-Content -LiteralPath $LogPath -Raw
if ($exitCode -ne 0 -or -not $logText.Contains('RABRON_WINDOWS_PLAYER_SMOKE_PASS')) {
    Get-Content -LiteralPath $LogPath -Tail 60
    throw "Windows Player startup failed: exit=$exitCode, expected real runtime pass marker."
}
Write-Host "Windows Player startup PASSED (exit 0). Log: $LogPath"
