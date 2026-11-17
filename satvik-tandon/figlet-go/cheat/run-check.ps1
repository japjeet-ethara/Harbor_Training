$ErrorActionPreference = 'Stop'

$taskRoot = Split-Path -Parent $PSScriptRoot
$solution = Join-Path $taskRoot 'solution'
$backupDir = Join-Path ([System.IO.Path]::GetTempPath()) "figlet-cheat-$PID"
New-Item -ItemType Directory -Path $backupDir | Out-Null

Copy-Item (Join-Path $solution 'solve.sh') (Join-Path $backupDir 'solve.sh')
try {
    Copy-Item (Join-Path $PSScriptRoot 'solve.sh') (Join-Path $solution 'solve.sh') -Force
    Copy-Item (Join-Path $PSScriptRoot 'visible.jsonl') (Join-Path $solution 'visible.jsonl') -Force
    harbor run -p $taskRoot -a oracle
}
finally {
    Copy-Item (Join-Path $backupDir 'solve.sh') (Join-Path $solution 'solve.sh') -Force
    Remove-Item (Join-Path $solution 'visible.jsonl') -ErrorAction SilentlyContinue
    Remove-Item $backupDir -Recurse -Force
}
