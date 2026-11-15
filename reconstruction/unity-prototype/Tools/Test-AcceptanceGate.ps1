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

        foreach ($bad in @($untrackedSource, $alternate)) {
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
        Write-Host 'PASS rejected: untracked Unity source and alternate scene; allowed Unity metadata/bootstrap scene'
    }
    finally {
        foreach ($file in @($meta, $untrackedSource, $alternate)) {
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
