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

# Do not launch this in the background or report success before Unity exits.
& $EditorPath @arguments
$exitCode = $LASTEXITCODE

if (-not (Test-Path -LiteralPath $log -PathType Leaf)) {
    throw "Unity did not create a log. Exit code: $exitCode"
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
