# Synthetic NUnit tests for the result gate. No Unity binary is invoked.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$validator = Join-Path $PSScriptRoot 'Assert-PlayModeResults.ps1'
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) (
    'rabron-nunit-gate-' + [Guid]::NewGuid().ToString('N')
)
[System.IO.Directory]::CreateDirectory($temporary) | Out-Null
$fixture = Join-Path $temporary 'result.xml'

$one = 'Rabron.Prototype.Tests.PlayModeFlowTests.SceneBootCreatesRuntimePlayerCameraHudAndStations'
$two = 'Rabron.Prototype.Tests.PlayModeFlowTests.HeistMarkersDriveFullLoopAndPhysicalCounterMoney'
$three = 'Rabron.Prototype.Tests.PlayModeFlowTests.UnreadableCheckpointsMustSurviveLaterAutosaves'

function New-TestCase([string]$name, [string]$result = 'Passed') {
    return '<test-case fullname="' + $name + '" result="' + $result + '" />'
}

function Write-Result(
    [string[]]$cases,
    [int]$total,
    [int]$passed,
    [int]$failed,
    [string]$result = 'Passed'
) {
    $body = $cases -join [Environment]::NewLine
    $xml = '<test-run total="' + $total + '" passed="' + $passed +
        '" failed="' + $failed + '" result="' + $result +
        '"><test-suite>' + $body + '</test-suite></test-run>'
    Set-Content -LiteralPath $fixture -Value $xml -Encoding utf8
}

function Assert-Accepted([string]$scenario, [int]$exitCode = 0) {
    try {
        & $validator -ResultsPath $fixture -UnityExitCode $exitCode | Out-Null
        Write-Host "PASS accepted: $scenario"
    }
    catch {
        throw "Expected acceptance for $scenario, but got: $_"
    }
}

function Assert-Rejected([string]$scenario, [int]$exitCode = 0) {
    $rejected = $false
    try {
        & $validator -ResultsPath $fixture -UnityExitCode $exitCode | Out-Null
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw "Expected rejection for $scenario; result was incorrectly accepted."
    }
    Write-Host "PASS rejected: $scenario"
}

try {
    # A clean-looking two-test report is no longer sufficient: data-loss
    # recovery must have actually run, not merely exist as Unity test source.
    $validCases = @((New-TestCase $one), (New-TestCase $two), (New-TestCase $three))
    Write-Result $validCases 3 3 0
    Assert-Accepted 'all three named tests passed'

    Assert-Rejected 'Unity process failed despite green XML' 2

    Write-Result $validCases 3 3 0 'Failed'
    Assert-Rejected 'NUnit run marked failed'

    Write-Result @() 0 0 0
    Assert-Rejected 'zero-test run'

    Write-Result @((New-TestCase $one), (New-TestCase $three)) 2 2 0
    Assert-Rejected 'second named test missing'

    Write-Result @((New-TestCase $one), (New-TestCase $two)) 2 2 0
    Assert-Rejected 'green two-case report missing mandatory save-recovery test'

    Write-Result @((New-TestCase $one), (New-TestCase $two),
                   (New-TestCase 'Some.Other.Test')) 3 3 0
    Assert-Rejected 'unrelated third test cannot replace save recovery'

    Write-Result @((New-TestCase $one), (New-TestCase $one),
                   (New-TestCase $two), (New-TestCase $three)) 4 4 0
    Assert-Rejected 'duplicate expected case'

    Write-Result @((New-TestCase $one), (New-TestCase $two),
                   (New-TestCase $three 'Failed')) 3 3 0
    Assert-Rejected 'failed save-recovery case hidden by green summary'

    Write-Result @((New-TestCase $one), (New-TestCase $two),
                   (New-TestCase $three 'Skipped')) 3 3 0
    Assert-Rejected 'skipped save-recovery case hidden by green summary'

    Write-Result $validCases 3 2 0
    Assert-Rejected 'passed count smaller than total'

    Write-Result $validCases 4 4 0
    Assert-Rejected 'total mismatches case count'

    Write-Result $validCases 3 2 1 'Failed'
    Assert-Rejected 'failure count is nonzero'

    Set-Content -LiteralPath $fixture -Value '<test-run invalid' -Encoding utf8
    Assert-Rejected 'malformed NUnit XML'

    Remove-Item -LiteralPath $fixture -Force
    Assert-Rejected 'missing result file'
}
finally {
    Remove-Item -LiteralPath $temporary -Recurse -Force
}
