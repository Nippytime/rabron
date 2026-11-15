# Git provenance for ALL untracked, nonignored Unity acceptance inputs.
# Unity also imports the local reconstruction/game/Core package. A clean
# tracked tree is insufficient if untracked packages, settings, tools or C#
# files can change a build without appearing in the recorded Git revision.
# Import-generated Assets/*.meta and the known bootstrap scene are allowed.
[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

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
