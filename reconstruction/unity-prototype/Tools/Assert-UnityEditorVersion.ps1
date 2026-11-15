# Query the actual Unity executable: a project settings value or path is
# not evidence that the correct Editor binary performed acceptance.
# Official Unity command line: -version prints version without starting Editor.
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$EditorPath,
    [Parameter(Mandatory)]
    [string]$ProjectVersionPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$required = '6000.5.0f1'
if (-not (Test-Path -LiteralPath $EditorPath -PathType Leaf)) {
    throw "Unity Editor missing: $EditorPath"
}
if (-not (Test-Path -LiteralPath $ProjectVersionPath -PathType Leaf)) {
    throw "Unity project version file missing: $ProjectVersionPath"
}

$projectText = Get-Content -LiteralPath $ProjectVersionPath -Raw
$configured = [regex]::Match(
    $projectText, '(?m)^m_EditorVersion:\s*([^\s]+)\s*$')
if (-not $configured.Success -or $configured.Groups[1].Value -cne $required) {
    throw "Project must target Unity $required; configured version is '$($configured.Groups[1].Value)'."
}

# Accept exactly one Unity-style version token and a successful native exit.
# Reject ambiguous output (multiple versions), wrong builds or failed probes.
$reported = (& $EditorPath -version 2>&1 | Out-String).Trim()
$code = $LASTEXITCODE
$versions = [regex]::Matches(
    $reported, '(?<![A-Za-z0-9.])\d+\.\d+\.\d+[abfp]\d+(?![A-Za-z0-9.])')
if ($code -ne 0 -or $versions.Count -ne 1 -or
    $versions[0].Value -cne $required) {
    throw "Actual Unity executable version verification failed: exit=$code; output='$reported'; required=$required."
}

# The calling acceptance runner records the attested binary version.
Write-Output $required
