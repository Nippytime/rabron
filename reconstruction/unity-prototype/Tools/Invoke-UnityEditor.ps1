# Unity.exe is a Windows GUI executable. PowerShell's native '&' call can
# return before Editor work has finished, leaving a misleading exit 0 and no
# -logFile. Start-Process -Wait waits for the launched process tree.
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$EditorPath,
    [Parameter(Mandatory)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Start-Process joins ArgumentList with spaces, so explicitly quote values
# containing whitespace; otherwise -projectPath/-logFile can be split.
$quoted = foreach ($argument in $Arguments) {
    if ($argument.Contains('"')) {
        throw 'Unity Editor arguments must not contain embedded quotes.'
    }
    if ($argument -match '\s') {
        '"' + $argument + '"'
    }
    else {
        $argument
    }
}

$process = Start-Process -FilePath $EditorPath -ArgumentList ($quoted -join ' ') `
    -PassThru -Wait
try {
    Write-Output ([int]$process.ExitCode)
}
finally {
    $process.Dispose()
}
