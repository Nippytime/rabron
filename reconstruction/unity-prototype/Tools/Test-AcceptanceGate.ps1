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
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
