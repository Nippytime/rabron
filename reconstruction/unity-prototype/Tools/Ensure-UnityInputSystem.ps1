# Enable Unity Input System on a generated PlayerSettings file without
# overwriting unrelated project configuration or Git-tracked settings.
# Invoked from the real Windows acceptance preflight before Editor smoke.
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectRoot,
    [Parameter(Mandatory)]
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$expectedProject = Join-Path $repo 'reconstruction/unity-prototype'
if (-not [string]::Equals($project, $expectedProject,
                         [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Unity Input System preflight requires the checked-out Rabron project.'
}

$settings = Join-Path $project 'ProjectSettings/ProjectSettings.asset'
if (-not (Test-Path -LiteralPath $settings -PathType Leaf)) {
    throw "Unity-generated PlayerSettings missing: $settings. Import the project using Unity 6000.5.0f1 first."
}

$raw = [IO.File]::ReadAllBytes($settings)
$text = [Text.Encoding]::UTF8.GetString($raw)
# Unity writes this setting once in YAML. Reject missing/multiple/unexpected
# values instead of inserting or silently overriding an unknown layout.
$matches = [regex]::Matches(
    $text, '(?m)^[ \t]*activeInputHandler[ \t]*:[ \t]*([0-9]+)[ \t]*\r?$')
if ($matches.Count -ne 1) {
    throw "Expected exactly one Unity activeInputHandler setting in $settings; found $($matches.Count)."
}
$valueGroup = $matches[0].Groups[1]
$value = $valueGroup.Value
if ($value -cne '0' -and $value -cne '1' -and $value -cne '2') {
    throw "Unsupported Unity activeInputHandler '$value' in $settings."
}
if ($value -ne '0') {
    Write-Host "Unity Input System already enabled (activeInputHandler=$value)."
    return
}

# Prevent changing tracked project settings behind Git HEAD provenance.
$relative = 'reconstruction/unity-prototype/ProjectSettings/ProjectSettings.asset'
$tracked = @(& git -C $repo ls-files -- $relative)
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect tracked Unity project settings.'
}
if ($tracked.Count -ne 0) {
    throw 'Unity Input System is disabled in Git-tracked PlayerSettings; update it in a reviewed commit instead.'
}

# Change only the ASCII 0 to 1, preserving every other byte, BOM and newline.
# Store an original-byte backup in the already-ignored project Logs folder.
$offset = [Text.Encoding]::UTF8.GetByteCount($text.Substring(0, $valueGroup.Index))
if ($offset -ge $raw.Length -or $raw[$offset] -ne [byte][char]'0') {
    throw 'Unity Input System settings are not UTF-8 YAML as expected.'
}
$replacement = [byte[]]$raw.Clone()
$replacement[$offset] = [byte][char]'1'
$backupDir = Join-Path $project 'Logs'
[IO.Directory]::CreateDirectory($backupDir) | Out-Null
$backup = Join-Path $backupDir ('ProjectSettings-before-input-system-' +
    [guid]::NewGuid().ToString('N') + '.asset')
[IO.File]::WriteAllBytes($backup, $raw)
try {
    [IO.File]::WriteAllBytes($settings, $replacement)
}
catch {
    [IO.File]::WriteAllBytes($settings, $raw)
    throw
}
if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($settings)) -cne
    [Convert]::ToBase64String($replacement)) {
    throw "Unity PlayerSettings verification failed; original copy retained in $backup."
}
Write-Host "Unity Input System enabled (activeInputHandler=1). Original settings backed up: $backup"
