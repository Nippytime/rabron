# Git provenance for ALL untracked, nonignored Unity acceptance inputs.
# Unity also imports the local reconstruction/game/Core package. A clean
# tracked tree is insufficient if untracked packages, settings, tools or C#
# files can change a build without appearing in the recorded Git revision.
# Import-generated Assets/*.meta and the known bootstrap scene are allowed.
[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../..')).Path,
    [string]$ExpectedRevision
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

# A clean worktree alone does not prove that lengthy Unity operations ran
# against the same commit. Revalidate the initial SHA at every boundary.
if ($ExpectedRevision) {
    if ($ExpectedRevision -cnotmatch '^[0-9a-f]{40} @(& git -C $RepoRoot ls-files --others --exclude-standard -- `
    reconstruction/unity-prototype reconstruction/game/Core)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect untracked Unity project and linked core inputs.'
}

$assetsPrefix = 'reconstruction/unity-prototype/Assets/'
$bootstrapScene = $assetsPrefix + 'Scenes/Prototype.unity'
$unexpected = @($untracked | Where-Object {
    $relative = $_.Trim('"').Replace('\', '/')
    $generatedMeta = $relative.StartsWith($assetsPrefix, [StringComparison]::Ordinal) -and
        $relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase)
    -not ($generatedMeta -or
          [string]::Equals($relative, $bootstrapScene,
                           [StringComparison]::Ordinal))
})
if ($unexpected.Count -gt 0) {
    throw ('Untracked Unity acceptance inputs are not covered by Git HEAD: ' +
           ($unexpected -join ', ') +
           '. Commit or remove these files before real acceptance.')
}

Write-Host 'Unity project and linked core provenance PASSED (known generated files excepted).'
) {
        throw 'Expected Unity acceptance Git revision must be a 40-character SHA.'
    }
    $actualRevision = (& git -C $RepoRoot rev-parse --verify HEAD)
    if ($LASTEXITCODE -ne 0 -or
        $actualRevision -notmatch '^[0-9a-f]{40} @(& git -C $RepoRoot ls-files --others --exclude-standard -- `
    reconstruction/unity-prototype reconstruction/game/Core)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect untracked Unity project and linked core inputs.'
}

$assetsPrefix = 'reconstruction/unity-prototype/Assets/'
$bootstrapScene = $assetsPrefix + 'Scenes/Prototype.unity'
$unexpected = @($untracked | Where-Object {
    $relative = $_.Trim('"').Replace('\', '/')
    $generatedMeta = $relative.StartsWith($assetsPrefix, [StringComparison]::Ordinal) -and
        $relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase)
    -not ($generatedMeta -or
          [string]::Equals($relative, $bootstrapScene,
                           [StringComparison]::Ordinal))
})
if ($unexpected.Count -gt 0) {
    throw ('Untracked Unity acceptance inputs are not covered by Git HEAD: ' +
           ($unexpected -join ', ') +
           '. Commit or remove these files before real acceptance.')
}

Write-Host 'Unity project and linked core provenance PASSED (known generated files excepted).'
) {
        throw 'Cannot inspect Git HEAD during Unity acceptance.'
    }
    if ($actualRevision -cne $ExpectedRevision) {
        throw "Git HEAD changed during Unity acceptance: expected $ExpectedRevision, found $actualRevision."
    }
}

$untracked = @(& git -C $RepoRoot ls-files --others --exclude-standard -- `
    reconstruction/unity-prototype reconstruction/game/Core)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect untracked Unity project and linked core inputs.'
}

$assetsPrefix = 'reconstruction/unity-prototype/Assets/'
$bootstrapScene = $assetsPrefix + 'Scenes/Prototype.unity'
$unexpected = @($untracked | Where-Object {
    $relative = $_.Trim('"').Replace('\', '/')
    $generatedMeta = $relative.StartsWith($assetsPrefix, [StringComparison]::Ordinal) -and
        $relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase)
    -not ($generatedMeta -or
          [string]::Equals($relative, $bootstrapScene,
                           [StringComparison]::Ordinal))
})
if ($unexpected.Count -gt 0) {
    throw ('Untracked Unity acceptance inputs are not covered by Git HEAD: ' +
           ($unexpected -join ', ') +
           '. Commit or remove these files before real acceptance.')
}

Write-Host 'Unity project and linked core provenance PASSED (known generated files excepted).'
