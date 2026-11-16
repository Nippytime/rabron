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

    Set-FakeEditorVersion '6000.5.0f1' 0
    $confirmed = & $versionGate -EditorPath $fakeEditor -ProjectVersionPath $versionFile
    if ($confirmed -cne '6000.5.0f1') {
        throw 'Correct Unity Editor binary version was not attested.'
    }
    Write-Host 'PASS accepted: exact Unity Editor 6000.5.0f1 version'

    Set-FakeEditorVersion '6000.3.18f1' 0
    Assert-VersionRejected 'wrong installed version (previous editor)'
    Set-FakeEditorVersion '6000.5.0f1 6000.3.17f1' 0
    Assert-VersionRejected 'ambiguous version output'
    Set-FakeEditorVersion '6000.5.0f1' 3
    Assert-VersionRejected 'nonzero native version probe'
    Set-FakeEditorVersion 'not-a-version' 0
    Assert-VersionRejected 'missing version token'

    # Matching executable is insufficient if a stale Unity project still
    # targets the old Editor. This never alters the tracked ProjectVersion.txt.
    Set-FakeEditorVersion '6000.5.0f1' 0
    $staleProject = Join-Path $temp 'old-ProjectVersion.txt'
    Set-Content -LiteralPath $staleProject -Encoding ascii -Value 'm_EditorVersion: 6000.3.18f1'
    $rejectedProject = $false
    try {
        & $versionGate -EditorPath $fakeEditor -ProjectVersionPath $staleProject |
            Out-Null
    }
    catch { $rejectedProject = $true }
    if (-not $rejectedProject) {
        throw 'Stale Unity project version was falsely accepted.'
    }
    Write-Host 'PASS rejected: mismatched Unity project version'

    # Synthetic child process must finish before launcher returns, even
    # when a script path and Editor log path contain spaces. No Unity is run.
    $launcher = Join-Path $PSScriptRoot 'Invoke-UnityEditor.ps1'
    $fakeScript = Join-Path $temp 'Fake Editor With Spaces.ps1'
    $fakeLog = Join-Path $temp 'Editor log with spaces.log'
    Set-Content -LiteralPath $fakeScript -Encoding utf8 -Value @'
param([string]$LogFile, [int]$ExitCode = 0)
Start-Sleep -Milliseconds 250
if ($ExitCode -ne 0) { exit $ExitCode }
[System.IO.File]::WriteAllText($LogFile, 'SYNTHETIC_EDITOR_COMPLETED')
'@
    $powerShellExecutable = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    $passedExit = & $launcher -EditorPath $powerShellExecutable `
        -Arguments @('-NoProfile', '-File', $fakeScript, '-LogFile', $fakeLog)
    if ($passedExit -ne 0 -or
        -not (Test-Path -LiteralPath $fakeLog -PathType Leaf) -or
        (Get-Content -LiteralPath $fakeLog -Raw) -ne 'SYNTHETIC_EDITOR_COMPLETED') {
        throw 'Synchronous Unity process launcher lost delayed log or split a spaced argument.'
    }
    Write-Host 'PASS waited: synthetic Editor completed and wrote delayed spaced-path log'
    Remove-Item -LiteralPath $fakeLog -Force
    $failedExit = & $launcher -EditorPath $powerShellExecutable `
        -Arguments @('-NoProfile', '-File', $fakeScript,
                     '-LogFile', $fakeLog, '-ExitCode', '17')
    if ($failedExit -ne 17 -or (Test-Path -LiteralPath $fakeLog)) {
        throw 'Unity process launcher did not propagate native failure or invented a log.'
    }
    Write-Host 'PASS rejected: synthetic Editor returned nonzero without log'

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

    # Use the real checkout HEAD; do not mutate branches or commits in CI.
    $expectedHead = (& git -C $repoRoot rev-parse --verify HEAD)
    if ($LASTEXITCODE -ne 0 -or $expectedHead -notmatch '^[0-9a-f]{40}$') {
        throw 'Synthetic provenance test requires a valid Git HEAD.'
    }
    & $provenance -RepoRoot $repoRoot -ExpectedRevision $expectedHead | Out-Null
    Write-Host 'PASS accepted: matching Unity acceptance Git HEAD'

    $driftRejected = $false
    try {
        & $provenance -RepoRoot $repoRoot -ExpectedRevision ('0' * 40) | Out-Null
    }
    catch {
        $driftRejected = $_.Exception.Message -like '*Git HEAD changed during Unity acceptance*'
    }
    if (-not $driftRejected) {
        throw 'Mismatched Git HEAD did not fail provenance for the correct reason.'
    }
    Write-Host 'PASS rejected: changed Unity acceptance Git HEAD'

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

    # Create a disposable Git repository to emulate files Unity 6.5 creates
    # on first import. Never delete or alter a developer's actual Unity files.
    $fakeRepo = Join-Path $temp 'unity-generated-inputs-fixture'
    foreach ($part in @('reconstruction/unity-prototype/Assets',
                        'reconstruction/unity-prototype/Packages',
                        'reconstruction/unity-prototype/ProjectSettings',
                        'reconstruction/game/Core')) {
        [System.IO.Directory]::CreateDirectory((Join-Path $fakeRepo $part)) | Out-Null
    }
    & git -C $fakeRepo init -q
    if ($LASTEXITCODE -ne 0) { throw 'Cannot initialize generated-input test repository.' }
    & git -C $fakeRepo config user.email 'rabron-tests@example.invalid'
    & git -C $fakeRepo config user.name 'Rabron synthetic test'
    $coreSource = Join-Path $fakeRepo 'reconstruction/game/Core/HeistSession.cs'
    Set-Content -LiteralPath $coreSource -Value '// tracked test core'
    & git -C $fakeRepo add -- reconstruction/game/Core/HeistSession.cs
    & git -C $fakeRepo commit -q -m 'synthetic tracked Unity core'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot commit synthetic tracked core.' }
    $fakeHead = (& git -C $fakeRepo rev-parse --verify HEAD)
    $projectSettings = Join-Path $fakeRepo 'reconstruction/unity-prototype/ProjectSettings'
    $packages = Join-Path $fakeRepo 'reconstruction/unity-prototype/Packages'
    $coreMeta = $coreSource + '.meta'
    $lock = Join-Path $packages 'packages-lock.json'
    $settings = Join-Path $projectSettings 'AudioManager.asset'
    $assetMeta = Join-Path $fakeRepo 'reconstruction/unity-prototype/Assets/Generated.cs.meta'
    foreach ($item in @($coreMeta, $lock, $settings, $assetMeta)) {
        Set-Content -LiteralPath $item -Value ('synthetic generated input ' + $item)
    }
    $baseline = @(& $provenance -RepoRoot $fakeRepo -ExpectedRevision $fakeHead `
        -CaptureGeneratedInputs)
    if ($baseline.Count -ne 4 -or @($baseline | Where-Object {
            -not $_.sha256 -or $_.sha256.Length -ne 64
        }).Count -gt 0) {
        throw 'Unity-generated inputs did not produce a complete four-file SHA-256 snapshot.'
    }
    & $provenance -RepoRoot $fakeRepo -ExpectedRevision $fakeHead `
        -ExpectedGeneratedInputs $baseline | Out-Null
    Write-Host 'PASS accepted: known Unity-generated settings, lock, linked core .meta and asset .meta with SHA-256'

    $originalSettings = Get-Content -LiteralPath $settings -Raw
    Set-Content -LiteralPath $settings -Value 'changed settings contents'
    $rejected = $false
    try {
        & $provenance -RepoRoot $fakeRepo -ExpectedGeneratedInputs $baseline | Out-Null
    }
    catch { $rejected = $_.Exception.Message -like '*SHA-256 changed*' }
    if (-not $rejected) { throw 'Edited generated Unity settings escaped SHA-256 provenance.' }
    Set-Content -LiteralPath $settings -Value $originalSettings -NoNewline

    $extraAllowed = Join-Path $projectSettings 'QualitySettings.asset'
    Set-Content -LiteralPath $extraAllowed -Value 'new default settings'
    $rejected = $false
    try {
        & $provenance -RepoRoot $fakeRepo -ExpectedGeneratedInputs $baseline | Out-Null
    }
    catch { $rejected = $_.Exception.Message -like '*SHA-256 changed*' }
    if (-not $rejected) { throw 'New generated Unity settings escaped file-set provenance.' }
    Remove-Item -LiteralPath $extraAllowed -Force
    Write-Host 'PASS rejected: edited or added Unity-generated input after fingerprint'

    foreach ($bad in @(
        (Join-Path $projectSettings 'CustomSettings.asset'),
        (Join-Path $packages 'custom.json'),
        (Join-Path $fakeRepo 'reconstruction/game/Core/Untracked.cs.meta')
    )) {
        Set-Content -LiteralPath $bad -Value 'unknown untracked content'
        $rejected = $false
        try { & $provenance -RepoRoot $fakeRepo | Out-Null }
        catch { $rejected = $_.Exception.Message -like '*not covered by Git HEAD*' }
        Remove-Item -LiteralPath $bad -Force
        if (-not $rejected) {
            throw "Unknown generated-like Unity acceptance input was allowed: $bad"
        }
    }
    Write-Host 'PASS rejected: unknown Unity project settings, package files and orphan core .meta'

    # Synthetic PlayerSettings only; never run a real Unity Editor here.
    $preflight = Join-Path $PSScriptRoot 'Ensure-UnityInputSystem.ps1'
    $generatedPlayerSettings = Join-Path $projectSettings 'ProjectSettings.asset'
    $originalYaml = "PlayerSettings:`r`n  companyName: Rabron`r`n  activeInputHandler: 0`r`n  productName: Prototype`r`n"
    [IO.File]::WriteAllText($generatedPlayerSettings, $originalYaml,
        [Text.UTF8Encoding]::new($false))
    & $preflight -ProjectRoot (Join-Path $fakeRepo 'reconstruction/unity-prototype') `
        -RepoRoot $fakeRepo | Out-Null
    $updatedYaml = [IO.File]::ReadAllText($generatedPlayerSettings)
    $expectedYaml = $originalYaml.Replace('activeInputHandler: 0', 'activeInputHandler: 1')
    if ($updatedYaml -cne $expectedYaml) {
        throw 'Input System preflight changed settings other than its one backend digit.'
    }
    $backups = @(Get-ChildItem -LiteralPath (Join-Path $fakeRepo 'reconstruction/unity-prototype/Logs') `
        -Filter 'ProjectSettings-before-input-system-*.asset')
    if ($backups.Count -ne 1 -or
        [IO.File]::ReadAllText($backups[0].FullName) -cne $originalYaml) {
        throw 'Input System preflight did not preserve original PlayerSettings bytes.'
    }
    & $preflight -ProjectRoot (Join-Path $fakeRepo 'reconstruction/unity-prototype') `
        -RepoRoot $fakeRepo | Out-Null
    if (@(Get-ChildItem -LiteralPath $backups[0].DirectoryName -Filter '*.asset').Count -ne 1) {
        throw 'Already enabled Input System must not create a second backup.'
    }
    [IO.File]::WriteAllText($generatedPlayerSettings,
        $originalYaml.Replace('activeInputHandler: 0', 'activeInputHandler: 2'))
    & $preflight -ProjectRoot (Join-Path $fakeRepo 'reconstruction/unity-prototype') `
        -RepoRoot $fakeRepo | Out-Null
    if (-not ([IO.File]::ReadAllText($generatedPlayerSettings)).Contains('activeInputHandler: 2')) {
        throw 'Already enabled Both input backends should remain unmodified.'
    }
    Write-Host 'PASS configured: legacy input 0 -> new 1, backup preserved, enabled settings 1/2 idempotent'

    foreach ($badYaml in @(
        "PlayerSettings:`n  companyName: Rabron`n",
        "PlayerSettings:`n  activeInputHandler: 0`n  activeInputHandler: 2`n",
        "PlayerSettings:`n  activeInputHandler: 3`n"
    )) {
        [IO.File]::WriteAllText($generatedPlayerSettings, $badYaml)
        $rejected = $false
        try {
            & $preflight -ProjectRoot (Join-Path $fakeRepo 'reconstruction/unity-prototype') `
                -RepoRoot $fakeRepo | Out-Null
        }
        catch { $rejected = $true }
        if (-not $rejected -or
            [IO.File]::ReadAllText($generatedPlayerSettings) -cne $badYaml) {
            throw 'Malformed or duplicate Unity Input System configuration was not rejected safely.'
        }
    }
    [IO.File]::WriteAllText($generatedPlayerSettings, $originalYaml)
    & git -C $fakeRepo add -- reconstruction/unity-prototype/ProjectSettings/ProjectSettings.asset
    & git -C $fakeRepo commit -q -m 'synthetic tracked PlayerSettings'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot commit synthetic PlayerSettings.' }
    $trackedRejected = $false
    try {
        & $preflight -ProjectRoot (Join-Path $fakeRepo 'reconstruction/unity-prototype') `
            -RepoRoot $fakeRepo | Out-Null
    }
    catch { $trackedRejected = $_.Exception.Message -like '*Git-tracked PlayerSettings*' }
    if (-not $trackedRejected -or
        [IO.File]::ReadAllText($generatedPlayerSettings) -cne $originalYaml) {
        throw 'Git-tracked PlayerSettings must not be automatically modified.'
    }
    Write-Host 'PASS rejected: malformed and tracked PlayerSettings remain unchanged'
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
