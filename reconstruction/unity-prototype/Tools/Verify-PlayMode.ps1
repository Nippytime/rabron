# Run Unity Test Framework Play Mode acceptance tests against REAL Unity Editor.
# Unlike Verify-Unity.ps1, -runTests must NOT use -quit.
[CmdletBinding()]
param(
    [string]$EditorPath = $env:UNITY_EDITOR
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $EditorPath) {
    $EditorPath = Join-Path $env:ProgramFiles 'Unity\Hub\Editor\6000.5.0f1\Editor\Unity.exe'
}
if (-not (Test-Path -LiteralPath $EditorPath -PathType Leaf)) {
    throw "Unity 6000.5.0f1 Editor not found at '$EditorPath'. Install through Unity Hub or pass -EditorPath."
}
$EditorPath = (Resolve-Path -LiteralPath $EditorPath).Path

$logs = Join-Path $project 'Logs'
[System.IO.Directory]::CreateDirectory($logs) | Out-Null
$results = Join-Path $logs 'playmode-results.xml'
$log = Join-Path $logs 'playmode-tests.log'

# Stale results are not proof of this invocation's success.
foreach ($file in @($results, $log)) {
    if (Test-Path -LiteralPath $file) {
        Remove-Item -LiteralPath $file -Force
    }
}

$arguments = @(
    '-batchmode',
    '-projectPath', $project,
    '-runTests',
    '-testPlatform', 'PlayMode',
    '-testCategory', 'RabronPlayMode',
    '-testResults', $results,
    '-logFile', $log
)

Write-Host "Running real Unity Play Mode acceptance tests in $project"
Write-Host "Editor: $EditorPath"
& $EditorPath @arguments
$exitCode = $LASTEXITCODE

if (-not (Test-Path -LiteralPath $results -PathType Leaf)) {
    if (Test-Path -LiteralPath $log) {
        Get-Content -LiteralPath $log -Tail 80
    }
    throw "Unity returned $exitCode and did not produce Play Mode NUnit XML: $results"
}

try {
    & (Join-Path $PSScriptRoot 'Assert-PlayModeResults.ps1') `
        -ResultsPath $results -UnityExitCode $exitCode
    Write-Host "NUnit XML: $results"
    Write-Host "Editor log: $log"
}
catch {
    if (Test-Path -LiteralPath $log -PathType Leaf) {
        Get-Content -LiteralPath $log -Tail 80
    }
    throw
}
