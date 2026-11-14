# Evaluate an NUnit result produced by the real Unity Test Framework.
# This script validates output; it does not execute Unity.
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ResultsPath,
    [Parameter(Mandatory)]
    [int]$UnityExitCode
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Test-Path -LiteralPath $ResultsPath -PathType Leaf)) {
    throw "Unity did not produce Play Mode NUnit results: $ResultsPath"
}

[xml]$xml = Get-Content -LiteralPath $ResultsPath -Raw
$run = $xml.SelectSingleNode('/test-run')
if ($null -eq $run) {
    throw "NUnit test-run element is missing: $ResultsPath"
}

$total = [int]$run.GetAttribute('total')
$passed = [int]$run.GetAttribute('passed')
$failed = [int]$run.GetAttribute('failed')
$status = $run.GetAttribute('result')
$cases = @($xml.SelectNodes('//test-case'))

$expected = @(
    'Rabron.Prototype.Tests.PlayModeFlowTests.SceneBootCreatesRuntimePlayerCameraHudAndStations',
    'Rabron.Prototype.Tests.PlayModeFlowTests.HeistMarkersDriveFullLoopAndPhysicalCounterMoney'
)

$actual = @($cases | ForEach-Object { $_.GetAttribute('fullname') })
$missing = @($expected | Where-Object { $_ -notin $actual })
$duplicates = @($actual | Group-Object | Where-Object { $_.Count -gt 1 })
$failedCases = @($cases | Where-Object { $_.GetAttribute('result') -ne 'Passed' })

if ($UnityExitCode -ne 0 -or $status -ne 'Passed' -or
    $total -lt $expected.Count -or $passed -ne $total -or $failed -ne 0 -or
    $cases.Count -ne $total -or $missing.Count -gt 0 -or
    $duplicates.Count -gt 0 -or $failedCases.Count -gt 0) {
    throw "Unity Play Mode acceptance FAILED: exit=$UnityExitCode " +
          "result=$status total=$total passed=$passed failed=$failed " +
          "cases=$($cases.Count) missing=$($missing -join ', ') " +
          "duplicate=$($duplicates.Count) failedCases=$($failedCases.Count)."
}

Write-Host "Unity Play Mode NUnit results PASSED ($passed/$total)."
