# Requires Unity Hub Editor 6000.5.0f1 (or an explicit -EditorPath).
# Run while the same Unity project is NOT already open.
[CmdletBinding()]
param(
    [string]$EditorPath = $env:UNITY_EDITOR,
    [switch]$BuildWindows
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$editorVersion = '6000.5.0f1'

if (-not $EditorPath) {
    $EditorPath = Join-Path $env:ProgramFiles "Unity\Hub\Editor\$editorVersion\Editor\Unity.exe"
}
if (-not (Test-Path -LiteralPath $EditorPath -PathType Leaf)) {
    throw "Unity Editor not found at '$EditorPath'. Install $editorVersion in Unity Hub or supply -EditorPath / UNITY_EDITOR."
}
$EditorPath = (Resolve-Path -LiteralPath $EditorPath).Path

$logDir = Join-Path $project 'Logs'
[System.IO.Directory]::CreateDirectory($logDir) | Out-Null
$log = Join-Path $logDir 'editor-smoke.log'
if (Test-Path -LiteralPath $log) {
    Remove-Item -LiteralPath $log -Force
}

$method = 'Rabron.Prototype.Editor.PrototypeSmokeTest.ValidateProject'
$token = 'RABRON_UNITY_EDITOR_SMOKE_PASS'
if ($BuildWindows) {
    $method = 'Rabron.Prototype.Editor.PrototypeSmokeTest.ValidateAndBuildWindows'
    $token = 'RABRON_UNITY_WINDOWS_BUILD_PASS'
}

$arguments = @(
    '-batchmode',
    '-quit',
    '-projectPath', $project,
    '-executeMethod', $method,
    '-logFile', $log
)
if ($BuildWindows) {
    $arguments += @('-buildTarget', 'StandaloneWindows64')
}

Write-Host "Unity Editor: $EditorPath"
Write-Host "Project:      $project"
Write-Host "Action:       $method"

# Unity is a GUI executable: wait for the real process tree, not just a
# PowerShell native-command invocation that may detach immediately.
$exitCode = & (Join-Path $PSScriptRoot 'Invoke-UnityEditor.ps1') `
    -EditorPath $EditorPath -Arguments $arguments

if (-not (Test-Path -LiteralPath $log -PathType Leaf)) {
    $fallback = Join-Path $env:LOCALAPPDATA 'Unity\Editor\Editor.log'
    $packageLog = Join-Path $project 'Logs\upm.log'
    throw "Unity process ended (exit $exitCode) without creating fresh Editor log: $log. " +
          "Close any graphical Unity Editor already using this project. " +
          "Check the project Logs directory and fallback Editor log at $fallback " +
          "(Package Manager: $packageLog). No Editor smoke success is claimed."
}

$logText = Get-Content -LiteralPath $log -Raw
if ($exitCode -ne 0 -or -not $logText.Contains($token)) {
    Get-Content -LiteralPath $log -Tail 80
    throw "Unity verification failed (exit $exitCode; expected token '$token'). Full log: $log"
}

if ($BuildWindows) {
    $exe = Join-Path $project 'Builds\RabronPrototype.exe'
    $data = Join-Path $project 'Builds\RabronPrototype_Data'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $data -PathType Container)) {
        throw "Windows build reported success but executable/data are missing."
    }
    Write-Host "Windows EXE: $exe"
}

Write-Host "Unity verification PASSED. Log: $log"
