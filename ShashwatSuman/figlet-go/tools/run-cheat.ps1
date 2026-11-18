# Step 7 cheat check in one command (PowerShell, from the figlet-go folder):
#
#   powershell -ExecutionPolicy Bypass -File tools\run-cheat.ps1
#
# Swaps the cheat/ folder in as solution/, runs the oracle agent on it, ALWAYS
# restores the real solution (even if the run fails), then prints the scores.
# Expected: reward 0.1667 (build 1, no_python 0, behaviour 0) and no secret.
param([string]$JobName = "figlet-cheat-" + (Get-Date -Format "yyyyMMdd-HHmmss"))

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$task = Split-Path -Parent $PSScriptRoot
Set-Location $task

if (Test-Path "solution.real") {
    throw "solution.real already exists. Restore it first: Remove-Item -Recurse solution; Rename-Item solution.real solution"
}

Rename-Item "solution" "solution.real"
try {
    Copy-Item -Recurse "cheat" "solution"
    Write-Host "Running the CHEAT as job '$JobName' ..."
    harbor run -p . -a oracle -o ../jobs --job-name $JobName
}
finally {
    if (Test-Path "solution") { Remove-Item -Recurse -Force "solution" }
    Rename-Item "solution.real" "solution"
    Write-Host "Real solution/ restored."
}

$trial = Get-ChildItem "..\jobs\$JobName" -Directory | Select-Object -First 1
Write-Host ""
Get-Content "$($trial.FullName)\verifier\reward.json"
Write-Host ""
Get-Content "$($trial.FullName)\verifier\test-stdout.txt" | Select-String "build=|SECRET|No secret"
