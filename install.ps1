# Copies the agent, the two commands and the skills into ~/.claude.
# Replaces only folders and files with our names; everything else there is left alone.
param([string]$ClaudeDir = (Join-Path $HOME '.claude'))
$ErrorActionPreference = 'Stop'

$version = & python -c "import sys; print(sys.version_info >= (3, 11))" 2>$null
if ($version -ne 'True') {
    Write-Error 'Needs Python 3.11 or later on PATH as "python".'
}

foreach ($kind in 'agents', 'commands', 'skills') {
    $to = Join-Path $ClaudeDir $kind
    New-Item -ItemType Directory -Force $to | Out-Null
    foreach ($item in Get-ChildItem (Join-Path $PSScriptRoot $kind)) {
        $target = Join-Path $to $item.Name
        if (Test-Path $target) { Remove-Item -Recurse -Force $target }
        Copy-Item -Recurse $item.FullName $target
        Write-Host "installed $kind/$($item.Name)"
    }
}
Write-Host "Done. Start a new Claude Code session to pick them up."
