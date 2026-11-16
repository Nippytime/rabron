# Git provenance for ALL untracked, nonignored Unity acceptance inputs.
# Unity also imports the local reconstruction/game/Core package. A clean
# tracked tree is insufficient if untracked packages, settings, tools or C#
# files can change a build without appearing in the recorded Git revision.
# Import-generated Assets/*.meta and the known bootstrap scene are allowed.
[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../..')).Path,
    [string]$ExpectedRevision,
    [object[]]$ExpectedGeneratedInputs,
    [switch]$CaptureGeneratedInputs
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

# A clean checkout is insufficient if Git HEAD changes during long Editor,
# Play Mode and Windows Player operations. Compare with the start SHA.
if ($ExpectedRevision) {
    if ($ExpectedRevision -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Expected Unity acceptance Git revision must be a 40-character SHA.'
    }
    $actualRevision = (& git -C $RepoRoot rev-parse --verify HEAD)
    if ($LASTEXITCODE -ne 0 -or
        $actualRevision -notmatch '^[0-9a-f]{40}$') {
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

# Track only explicit Unity-generated inputs. Other untracked ProjectSettings,
# Packages, Tools and linked C# code remain disallowed. Unity creates default
# settings and a lock file on first import, and writes .meta files for the
# already tracked linked game core; those must be recorded, not discarded.
$assetsPrefix = 'reconstruction/unity-prototype/Assets/'
$corePrefix = 'reconstruction/game/Core/'
$settingsPrefix = 'reconstruction/unity-prototype/ProjectSettings/'
$bootstrapScene = $assetsPrefix + 'Scenes/Prototype.unity'
$packagesLock = 'reconstruction/unity-prototype/Packages/packages-lock.json'
# Only these generated URP 17.5 pipeline assets may remain untracked. They
# are created by our real Unity CLI method, never imported from game bundles,
# and their exact bytes are recorded before Play Mode/build and compared after.
$urpAssets = [System.Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
[void]$urpAssets.Add($assetsPrefix + 'Settings/RabronURP.asset')
[void]$urpAssets.Add($assetsPrefix + 'Settings/RabronRenderer.asset')
$defaultSettings = @(
    'AudioManager.asset',
    'ClusterInputManager.asset',
    'DynamicsManager.asset',
    'EditorBuildSettings.asset',
    'EditorSettings.asset',
    'GraphicsSettings.asset',
    'InputManager.asset',
    'MemorySettings.asset',
    'MultiplayerManager.asset',
    'NavMeshAreas.asset',
    'Physics2DSettings.asset',
    'PhysicsCoreProjectSettings2D.asset',
    'PresetManager.asset',
    'ProjectSettings.asset',
    'QualitySettings.asset',
    'TagManager.asset',
    'TimeManager.asset',
    'UnityConnectSettings.asset',
    'VFXManager.asset',
    'VersionControlSettings.asset'
)
$allowedSettings = [System.Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
foreach ($name in $defaultSettings) {
    [void]$allowedSettings.Add($settingsPrefix + $name)
}
$trackedCore = @(& git -C $RepoRoot ls-files -- reconstruction/game/Core)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect Git-tracked local Unity package sources.'
}
$trackedSet = [System.Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
foreach ($file in $trackedCore) {
    [void]$trackedSet.Add($file.Trim('"').Replace('\', '/'))
}

$unexpected = [System.Collections.Generic.List[string]]::new()
$generated = [System.Collections.Generic.List[string]]::new()
foreach ($file in $untracked) {
    $relative = $file.Trim('"').Replace('\', '/')
    $isAssetMeta = $relative.StartsWith($assetsPrefix, [StringComparison]::Ordinal) -and
        $relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase)
    $isCoreMeta = $relative.StartsWith($corePrefix, [StringComparison]::Ordinal) -and
        $relative.EndsWith('.meta', [StringComparison]::OrdinalIgnoreCase) -and
        $trackedSet.Contains($relative.Substring(0, $relative.Length - 5))
    $isGenerated = $isAssetMeta -or $isCoreMeta -or
        $allowedSettings.Contains($relative) -or
        $urpAssets.Contains($relative) -or
        [string]::Equals($relative, $packagesLock, [StringComparison]::Ordinal)
    if ([string]::Equals($relative, $bootstrapScene, [StringComparison]::Ordinal)) {
        continue # Generated scene is independently SHA-256 checked by the runner.
    }
    if ($isGenerated) {
        $generated.Add($relative)
    }
    else {
        $unexpected.Add($relative)
    }
}
if ($unexpected.Count -gt 0) {
    throw ('Untracked Unity acceptance inputs are not covered by Git HEAD: ' +
           ($unexpected -join ', ') +
           '. Commit or remove these files before real acceptance.')
}

# These files aren't Git-bound, so list their exact bytes and paths. Captured
# after real Editor import, then compared after Play Mode and Player build.
# A changed, removed or added generated file invalidates acceptance.
$snapshot = @($generated | Sort-Object -Unique | ForEach-Object {
    $relative = $_
    $path = Join-Path $RepoRoot ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
    $file = Get-Item -LiteralPath $path -ErrorAction Stop
    if (-not $file.PSIsContainer) {
        [pscustomobject][ordered]@{
            path = $relative
            bytes = [long]$file.Length
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    else {
        throw "Unity-generated acceptance input is not a file: $relative"
    }
})
if ($PSBoundParameters.ContainsKey('ExpectedGeneratedInputs')) {
    $expected = ConvertTo-Json -InputObject @($ExpectedGeneratedInputs) -Compress -Depth 5
    $actual = ConvertTo-Json -InputObject $snapshot -Compress -Depth 5
    if ($expected -cne $actual) {
        throw 'Unity-generated acceptance input file set or SHA-256 changed during validation.'
    }
}
Write-Host 'Unity project and linked core provenance PASSED (generated inputs fingerprinted).'
if ($CaptureGeneratedInputs) {
    foreach ($entry in $snapshot) {
        Write-Output $entry
    }
}
