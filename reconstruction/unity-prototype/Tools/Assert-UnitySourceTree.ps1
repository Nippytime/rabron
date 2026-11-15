# Git provenance for authored Unity Assets before/after real acceptance gates.
# Unity creates .meta files and the one known bootstrap scene on import.
# Untracked source, prefabs, resources, shaders and alternate scenes are NOT
# covered by a Git HEAD manifest and must never silently affect the build.
[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

$untracked = @(& git -C $RepoRoot ls-files --others --exclude-standard -- reconstruction/unity-prototype/Assets)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect untracked Unity source assets.'
}

$bootstrapScene = 'reconstruction/unity-prototype/Assets/Scenes/Prototype.unity'
$unexpected = @($untracked | Where-Object {
    $relative = $_.Trim('"').Replace('\', '/')
    -not ($relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase) -or
          [string]::Equals($relative, $bootstrapScene,
                           [StringComparison]::Ordinal))
})
if ($unexpected.Count -gt 0) {
    throw ('Untracked authored Unity assets are not covered by Git HEAD: ' +
           ($unexpected -join ', ') +
           '. Commit or remove these files before real acceptance.')
}

Write-Host 'Unity authored asset provenance PASSED (known generated files excepted).'
