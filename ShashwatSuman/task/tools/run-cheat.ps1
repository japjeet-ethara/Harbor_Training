# Step 7 cheat check in one command (PowerShell, from the titlecase-go folder):
#
#   powershell -ExecutionPolicy Bypass -File tools\run-cheat.ps1
#
# Swaps cheat/solve.sh in as the solution, runs the oracle agent on it,
# ALWAYS restores the real solution (even if the run fails), then prints
# the scores. Expected reward: 0.1667 (build 1, no_python 0, behaviour 0).
param([string]$JobName = "cheat-" + (Get-Date -Format "yyyyMMdd-HHmmss"))

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$task = Split-Path -Parent $PSScriptRoot
Set-Location $task

$real = "solution\solve.sh"
$backup = "solution\solve.sh.real"
if (Test-Path $backup) {
    throw "$backup already exists. Restore it first: Move-Item -Force $backup $real"
}

Copy-Item $real $backup
try {
    Copy-Item "cheat\solve.sh" $real -Force
    Write-Host "Running the CHEAT as job '$JobName' ..."
    harbor run -p . -a oracle -o ../jobs --job-name $JobName
}
finally {
    Move-Item -Force $backup $real
    Write-Host "Real solution/solve.sh restored."
}

$trial = Get-ChildItem "..\jobs\$JobName" -Directory | Select-Object -First 1
$details = Get-Content "$($trial.FullName)\verifier\reward-details.json" -Raw | ConvertFrom-Json
Write-Host ""
Write-Host ("cheat reward = {0}   (must be below 0.2)" -f $details.reward.score)
$details.reward.components | ForEach-Object { Write-Host ("  {0,-10} = {1}" -f $_.name, $_.detail.score) }
