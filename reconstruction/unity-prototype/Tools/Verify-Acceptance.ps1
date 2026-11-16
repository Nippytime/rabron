# Local, fail-closed Unity acceptance evidence. This requires real Windows Unity.
# Hosted Python/.NET CI does not invoke or satisfy this script.
[CmdletBinding()]
param(
    [string]$EditorPath = $env:UNITY_EDITOR,
    [string]$EvidencePath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$logs = Join-Path $project 'Logs'
[System.IO.Directory]::CreateDirectory($logs) | Out-Null
if (-not $EvidencePath) {
    $EvidencePath = Join-Path $logs 'unity-acceptance.json'
}
$evidenceFolder = [System.IO.Path]::GetDirectoryName(
    [System.IO.Path]::GetFullPath($EvidencePath))
[System.IO.Directory]::CreateDirectory($evidenceFolder) | Out-Null
$EvidencePath = [System.IO.Path]::GetFullPath($EvidencePath)

# Never let an old "passed" manifest survive a failed new invocation.
if (Test-Path -LiteralPath $EvidencePath) {
    Remove-Item -LiteralPath $EvidencePath -Force
}
$editorLogCopy = Join-Path $logs 'editor-acceptance-smoke.log'
if (Test-Path -LiteralPath $editorLogCopy) {
    Remove-Item -LiteralPath $editorLogCopy -Force
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'Real Unity acceptance requires a Windows host with Unity 6000.5.0f1.'
}

if (-not $EditorPath) {
    $EditorPath = Join-Path $env:ProgramFiles 'Unity\Hub\Editor\6000.5.0f1\Editor\Unity.exe'
}
if (-not (Test-Path -LiteralPath $EditorPath -PathType Leaf)) {
    throw "Unity Editor missing: $EditorPath"
}
$EditorPath = (Resolve-Path -LiteralPath $EditorPath).Path

# -EditorPath is user-supplied; ProjectVersion.txt cannot attest the binary.
# Unity -version is a real executable probe without opening the project.
$actualEditorVersion = & (Join-Path $PSScriptRoot 'Assert-UnityEditorVersion.ps1') `
    -EditorPath $EditorPath `
    -ProjectVersionPath (Join-Path $project 'ProjectSettings/ProjectVersion.txt')

# Bind every local result to an exact tracked revision, not a loose folder.
$revision = (& git -C $repoRoot rev-parse --verify HEAD)
if ($LASTEXITCODE -ne 0 -or
    $revision -notmatch '^[0-9a-f]{40}$') {
    throw 'Cannot establish a 40-character Git HEAD revision.'
}
$dirty = @(& git -C $repoRoot status --porcelain --untracked-files=no -- reconstruction)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) {
    throw 'Tracked reconstruction source is dirty; commit and retry before acceptance.'
}
& (Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1') -RepoRoot $repoRoot -ExpectedRevision $revision

# Unity 6.5 does not enable the new backend solely because the package is
# installed. A first import generates PlayerSettings; configure it before
# the separate smoke process so Unity reloads ENABLE_INPUT_SYSTEM.
$playerSettings = Join-Path $project 'ProjectSettings/ProjectSettings.asset'
if (-not (Test-Path -LiteralPath $playerSettings -PathType Leaf)) {
    $importLog = Join-Path $logs 'input-system-first-import.log'
    if (Test-Path -LiteralPath $importLog) {
        Remove-Item -LiteralPath $importLog -Force
    }
    $importCode = & (Join-Path $PSScriptRoot 'Invoke-UnityEditor.ps1') `
        -EditorPath $EditorPath `
        -Arguments @('-batchmode', '-quit', '-projectPath', $project,
                     '-logFile', $importLog)
    if ($importCode -ne 0 -or
        -not (Test-Path -LiteralPath $importLog -PathType Leaf) -or
        (Get-Item -LiteralPath $importLog).Length -eq 0) {
        throw "Unity first import failed (exit $importCode); inspect $importLog. No acceptance success claimed."
    }
}
& (Join-Path $PSScriptRoot 'Ensure-UnityInputSystem.ps1') `
    -ProjectRoot $project -RepoRoot $repoRoot
$dirtyAfterInput = @(& git -C $repoRoot status --porcelain --untracked-files=no -- reconstruction)
if ($LASTEXITCODE -ne 0 -or $dirtyAfterInput.Count -gt 0) {
    throw 'Unity Input System preflight modified tracked reconstruction inputs.'
}
& (Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1') -RepoRoot $repoRoot -ExpectedRevision $revision

function Assert-NonemptyFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Acceptance evidence missing: $path"
    }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -le 0) {
        throw "Acceptance evidence is empty: $path"
    }
    return $item
}

function File-Summary([string]$path) {
    $item = Assert-NonemptyFile $path
    return [ordered]@{
        name = $item.Name
        bytes = [long]$item.Length
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$startedUtc = (Get-Date).ToUniversalTime()
$smoke = Join-Path $logs 'editor-smoke.log'
$playmodeResults = Join-Path $logs 'playmode-results.xml'
$playmodeLog = Join-Path $logs 'playmode-tests.log'
$playerLog = Join-Path $logs 'windows-player-smoke.log'
$exe = Join-Path $project 'Builds\RabronPrototype.exe'
$data = Join-Path $project 'Builds\RabronPrototype_Data'
$scene = Join-Path $project 'Assets/Scenes/Prototype.unity'

# These existing runners each independently require a real Unity exit
# code plus a valid fresh log/expected token or actual NUnit result.
& (Join-Path $PSScriptRoot 'Verify-Unity.ps1') -EditorPath $EditorPath
Assert-NonemptyFile $smoke | Out-Null
Copy-Item -LiteralPath $smoke -Destination $editorLogCopy
# The Editor intentionally generates its single bootstrap scene. It is not
# Git-tracked; fingerprint the actual scene used by every subsequent gate.
$sceneAtSmoke = File-Summary $scene
$generatedInputs = @(& (Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1') `
    -RepoRoot $repoRoot -ExpectedRevision $revision -CaptureGeneratedInputs)
& (Join-Path $PSScriptRoot 'Verify-PlayMode.ps1') -EditorPath $EditorPath
& (Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1') `
    -RepoRoot $repoRoot -ExpectedRevision $revision -ExpectedGeneratedInputs $generatedInputs
if ((File-Summary $scene).sha256 -ne $sceneAtSmoke.sha256) {
    throw 'Generated Unity scene changed after the Editor smoke gate.'
}
Assert-NonemptyFile $playmodeResults | Out-Null
Assert-NonemptyFile $playmodeLog | Out-Null

$oldExe = Get-Item -LiteralPath $exe -ErrorAction SilentlyContinue
$buildStartedUtc = (Get-Date).ToUniversalTime()
& (Join-Path $PSScriptRoot 'Verify-Unity.ps1') -EditorPath $EditorPath -BuildWindows
$newExe = Assert-NonemptyFile $exe
if ($oldExe -and $newExe.LastWriteTimeUtc -le $oldExe.LastWriteTimeUtc) {
    throw 'Windows executable was not regenerated by the current build.'
}
if ($newExe.LastWriteTimeUtc -lt $buildStartedUtc.AddSeconds(-2)) {
    throw 'Windows executable predates the current build invocation.'
}
if (-not (Test-Path -LiteralPath $data -PathType Container) -or
    @(Get-ChildItem -LiteralPath $data -File -Recurse).Count -eq 0) {
    throw 'Windows build data directory is absent or empty.'
}

# The built EXE must actually start and exit cleanly, not merely exist.
# The runner deletes stale logs, limits execution time and checks an
# opt-in runtime marker emitted only by the built Player after bootstrap.
& (Join-Path $PSScriptRoot 'Verify-WindowsPlayer.ps1') `
    -ExePath $exe -LogPath $playerLog
Assert-NonemptyFile $playerLog | Out-Null

# Git should not have mutated tracked source/settings during the real
# Unity Editor/Play Mode/build/Player invocations; HEAD remains provenance.
$dirtyAfter = @(& git -C $repoRoot status --porcelain --untracked-files=no -- reconstruction)
if ($LASTEXITCODE -ne 0 -or $dirtyAfter.Count -gt 0) {
    throw 'Unity modified tracked reconstruction files; review changes before acceptance.'
}
& (Join-Path $PSScriptRoot 'Assert-UnitySourceTree.ps1') `
    -RepoRoot $repoRoot -ExpectedRevision $revision -ExpectedGeneratedInputs $generatedInputs
if ((File-Summary $scene).sha256 -ne $sceneAtSmoke.sha256) {
    throw 'Generated Unity scene changed after the Windows build gate.'
}

[xml]$xml = Get-Content -LiteralPath $playmodeResults -Raw
$run = $xml.SelectSingleNode('/test-run')
if ($null -eq $run -or $run.GetAttribute('result') -ne 'Passed') {
    throw 'Post-run NUnit evidence no longer reports success.'
}
$testCount = [int]$run.GetAttribute('total')
$passedCount = [int]$run.GetAttribute('passed')
if ($testCount -lt 3 -or $testCount -ne $passedCount) {
    throw 'Play Mode test count is inconsistent with the required tests.'
}

$manifest = [ordered]@{
    schema_version = 1
    scope = 'local Windows Unity Editor, Play Mode, build and headless Player startup; manual gameplay not verified'
    git_revision = $revision
    generated_inputs_fingerprinted_after_editor_smoke = $true
    generated_untracked_inputs = @($generatedInputs)
    started_utc = $startedUtc.ToString('o')
    finished_utc = (Get-Date).ToUniversalTime().ToString('o')
    editor_executable = $EditorPath
    actual_editor_version = $actualEditorVersion
    configured_editor_version = (Get-Content -LiteralPath (
        Join-Path $project 'ProjectSettings\ProjectVersion.txt') -Raw).Trim()
    automatic_gates_passed = $true
    manual_playthrough_verified = $false
    windows_player_smoke_passed = $true
    playmode_total = $testCount
    playmode_passed = $passedCount
    artifacts = [ordered]@{
        generated_scene = $sceneAtSmoke
        editor_smoke_log = File-Summary $editorLogCopy
        playmode_nunit_xml = File-Summary $playmodeResults
        playmode_editor_log = File-Summary $playmodeLog
        windows_build_log = File-Summary $smoke
        windows_executable = File-Summary $exe
        windows_player_smoke_log = File-Summary $playerLog
    }
    windows_data_directory_present = $true
}

# Only after all three real gates pass: write an atomic local manifest.
$json = $manifest | ConvertTo-Json -Depth 8
$temp = $EvidencePath + '.tmp'
try {
    [System.IO.File]::WriteAllText($temp, $json, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temp -Destination $EvidencePath -Force
}
finally {
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Force
    }
}
Write-Host "Real Unity automated acceptance PASSED at revision $revision"
Write-Host "Evidence manifest: $EvidencePath"
Write-Host 'Manual rendered Windows gameplay and visual/control validation remain REQUIRED.'
