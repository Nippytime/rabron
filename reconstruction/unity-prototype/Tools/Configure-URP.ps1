# Uses the *real* installed Unity CLI to migrate the prototype to URP.
# Not an alternative to Verify-Acceptance.ps1 (Editor, NUnit, build, Player).
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$unity = Get-Command unity -ErrorAction SilentlyContinue
if ($null -eq $unity) {
    throw 'Unity CLI is not installed/on PATH. Install the official unity CLI; Get-Command unity must succeed.'
}
$head = & git -C $repoRoot rev-parse --verify HEAD
if ($LASTEXITCODE -ne 0 -or $head -notmatch '^[0-9a-f]{40}$') {
    throw 'Cannot establish a Git HEAD revision for URP migration.'
}
$dirty = @(& git -C $repoRoot status --porcelain --untracked-files=no -- reconstruction)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) {
    throw 'Tracked reconstruction files are dirty; inspect the changes before running URP migration.'
}
$provenance = Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1'
& $provenance -RepoRoot $repoRoot -ExpectedRevision $head

$logs = Join-Path $project 'Logs'
[IO.Directory]::CreateDirectory($logs) | Out-Null
$log = Join-Path $logs 'urp-configure.log'
if (Test-Path -LiteralPath $log) {
    Remove-Item -LiteralPath $log -Force
}

& $unity.Source run $project --editor-version '6000.5.0f1' --log-file $log -- `
    -executeMethod 'Rabron.Prototype.Editor.PrototypeUrpSetup.Configure'
$code = $LASTEXITCODE
if ($code -ne 0 -or
    -not (Test-Path -LiteralPath $log -PathType Leaf) -or
    (Get-Item -LiteralPath $log).Length -eq 0) {
    if (Test-Path -LiteralPath $log) {
        Get-Content -LiteralPath $log -Tail 60
    }
    throw "Unity CLI URP setup failed (exit $code) or did not write a fresh Editor log: $log"
}
$contents = Get-Content -LiteralPath $log -Raw
if (-not $contents.Contains('RABRON_URP_CONFIGURED_PASS')) {
    Get-Content -LiteralPath $log -Tail 60
    throw "Unity CLI finished without the real URP configuration success token: $log"
}
$dirtyAfter = @(& git -C $repoRoot status --porcelain --untracked-files=no -- reconstruction)
if ($LASTEXITCODE -ne 0 -or $dirtyAfter.Count -gt 0) {
    throw 'Unity CLI modified tracked reconstruction files; inspect these changes before acceptance.'
}
& $provenance -RepoRoot $repoRoot -ExpectedRevision $head
Write-Host "Real Unity CLI URP setup PASSED at Git revision $head. Editor log: $log"
