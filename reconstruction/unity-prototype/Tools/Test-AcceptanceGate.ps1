# Synthetic failure-gate test; deliberately never invokes a real Unity Editor.
# Proves stale success manifests cannot survive a rejected invocation.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$runner = Join-Path $PSScriptRoot 'Verify-Acceptance.ps1'
$temp = Join-Path ([System.IO.Path]::GetTempPath()) (
    'rabron-unity-acceptance-' + [Guid]::NewGuid().ToString('N')
)
[System.IO.Directory]::CreateDirectory($temp) | Out-Null

try {
    # Probe a real executable path through synthetic native shims only;
    # CI has no licensed Unity. Wrong/ambiguous versions and failed probes
    # must be rejected before a local acceptance run can begin.
    $versionGate = Join-Path $PSScriptRoot 'Assert-UnityEditorVersion.ps1'
    $versionFile = Join-Path $PSScriptRoot '../ProjectSettings/ProjectVersion.txt'
    $windows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
    $fakeEditor = Join-Path $temp $(if ($windows) { 'fake-unity.cmd' } else { 'fake-unity.sh' })

    function Set-FakeEditorVersion([string]$value, [int]$code) {
        if ($windows) {
            Set-Content -LiteralPath $fakeEditor -Encoding ascii -Value @(
                '@echo off', "echo $value", "exit /b $code")
        }
        else {
            Set-Content -LiteralPath $fakeEditor -Encoding ascii -Value @(
                '#!/bin/sh', "printf '%s\n' '$value'", "exit $code")
            & chmod +x $fakeEditor
            if ($LASTEXITCODE -ne 0) { throw 'Cannot create synthetic executable.' }
        }
    }

    function Assert-VersionRejected([string]$scenario) {
        $rejected = $false
        try {
            & $versionGate -EditorPath $fakeEditor -ProjectVersionPath $versionFile |
                Out-Null
        }
        catch { $rejected = $true }
        if (-not $rejected) {
            throw "Expected Unity Editor version rejection: $scenario"
        }
        Write-Host "PASS rejected: Unity Editor $scenario"
    }

    Set-FakeEditorVersion '6000.3.18f1' 0
    $confirmed = & $versionGate -EditorPath $fakeEditor -ProjectVersionPath $versionFile
    if ($confirmed -cne '6000.3.18f1') {
        throw 'Correct Unity Editor binary version was not attested.'
    }
    Write-Host 'PASS accepted: exact Unity Editor 6000.3.18f1 version'

    Set-FakeEditorVersion '6000.3.17f1' 0
    Assert-VersionRejected 'wrong installed version'
    Set-FakeEditorVersion '6000.3.18f1 6000.3.17f1' 0
    Assert-VersionRejected 'ambiguous version output'
    Set-FakeEditorVersion '6000.3.18f1' 3
    Assert-VersionRejected 'nonzero native version probe'
    Set-FakeEditorVersion 'not-a-version' 0
    Assert-VersionRejected 'missing version token'

    $evidence = Join-Path $temp 'unity-acceptance.json'
    Set-Content -LiteralPath $evidence -Value '{"automatic_gates_passed":true}' -Encoding utf8
    $nonexistent = Join-Path $temp 'nonexistent-unity-editor.exe'
    $rejected = $false
    try {
        & $runner -EditorPath $nonexistent -EvidencePath $evidence | Out-Null
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw 'Missing real Windows Unity was falsely accepted.'
    }
    if (Test-Path -LiteralPath $evidence) {
        throw 'Stale green Unity acceptance evidence survived a failed invocation.'
    }
    Write-Host 'PASS rejected: missing Unity platform/editor and stale success removed'

    # A previously green runtime log must never survive a failed player
    # invocation. This deliberately supplies a missing EXE (no Unity run).
    $playerRunner = Join-Path $PSScriptRoot 'Verify-WindowsPlayer.ps1'
    $playerLog = Join-Path $temp 'windows-player-smoke.log'
    Set-Content -LiteralPath $playerLog -Value 'RABRON_WINDOWS_PLAYER_SMOKE_PASS'
    $rejected = $false
    try {
        & $playerRunner -ExePath (Join-Path $temp 'missing-player.exe') `
            -LogPath $playerLog | Out-Null
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw 'Missing real Windows Player was falsely accepted.'
    }
    if (Test-Path -LiteralPath $playerLog) {
        throw 'Stale green Windows Player log survived a failed invocation.'
    }
    Write-Host 'PASS rejected: missing Windows Player and stale startup marker removed'

    # Synthetic Git-based provenance tests: NO Unity executable is launched.
    $provenance = Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1'
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
    $assets = Join-Path $repoRoot 'reconstruction/unity-prototype/Assets'
    $nonce = 'acceptance-provenance-' + [Guid]::NewGuid().ToString('N')
    $meta = Join-Path $assets ($nonce + '.meta')
    $untrackedSource = Join-Path $assets ($nonce + '.cs')
    $sceneFolder = Join-Path $assets 'Scenes'
    $scene = Join-Path $sceneFolder 'Prototype.unity'
    $alternate = Join-Path $sceneFolder ($nonce + '.unity')
    $untrackedPackage = Join-Path $repoRoot (
        'reconstruction/unity-prototype/Packages/' + $nonce + '.json')
    $untrackedSettings = Join-Path $repoRoot (
        'reconstruction/unity-prototype/ProjectSettings/' + $nonce + '.asset')
    $untrackedTool = Join-Path $repoRoot (
        'reconstruction/unity-prototype/Tools/' + $nonce + '.ps1')
    $untrackedCore = Join-Path $repoRoot (
        'reconstruction/game/Core/' + $nonce + '.cs')
    $unexpectedInputs = @($untrackedSource, $alternate, $untrackedPackage,
                          $untrackedSettings, $untrackedTool, $untrackedCore)
    $createdScene = $false
    $createdSceneFolder = $false

    try {
        & $provenance -RepoRoot $repoRoot | Out-Null

        Set-Content -LiteralPath $meta -Value 'synthetic Unity import metadata'
        & $provenance -RepoRoot $repoRoot | Out-Null

        if (-not (Test-Path -LiteralPath $sceneFolder)) {
            New-Item -ItemType Directory -Path $sceneFolder | Out-Null
            $createdSceneFolder = $true
        }
        if (-not (Test-Path -LiteralPath $scene)) {
            Set-Content -LiteralPath $scene -Value 'synthetic bootstrap scene'
            $createdScene = $true
        }
        & $provenance -RepoRoot $repoRoot | Out-Null

        # Test every untracked input that may change the real Editor import,
        # tests or linked game core without changing the recorded Git HEAD.
        foreach ($bad in $unexpectedInputs) {
            Set-Content -LiteralPath $bad -Value 'synthetic untracked source'
            $rejected = $false
            try {
                & $provenance -RepoRoot $repoRoot | Out-Null
            }
            catch {
                $rejected = $true
            }
            Remove-Item -LiteralPath $bad -Force
            if (-not $rejected) {
                throw "Untracked authored Unity file was incorrectly accepted: $bad"
            }
        }

        & $provenance -RepoRoot $repoRoot | Out-Null
        Write-Host 'PASS rejected: untracked Assets, Packages, ProjectSettings, Tools and linked core; allowed generated metadata/bootstrap scene'
    }
    finally {
        foreach ($file in @($meta) + $unexpectedInputs) {
            if (Test-Path -LiteralPath $file) {
                Remove-Item -LiteralPath $file -Force
            }
        }
        if ($createdScene -and (Test-Path -LiteralPath $scene)) {
            Remove-Item -LiteralPath $scene -Force
        }
        if ($createdSceneFolder) {
            Remove-Item -LiteralPath $sceneFolder -Force -ErrorAction SilentlyContinue
        }
    }
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
