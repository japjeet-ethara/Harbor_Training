param([Parameter(Mandatory=$true)][string]$RunPath,[Parameter(Mandatory=$true)][string]$Baseline)
$ErrorActionPreference='Stop'
$Host.UI.RawUI.WindowTitle="Komal Harbor - $Baseline"
Clear-Host
$reward=Get-ChildItem -LiteralPath (Join-Path $RunPath "jobs/$Baseline") -Filter reward.json -Recurse
if (@($reward).Count -ne 1) { throw 'Expected one genuine Harbor reward file' }
Write-Host "Komal | Harbor Task 1 | $Baseline" -ForegroundColor Cyan
Write-Host 'Post-run terminal view of saved Harbor verifier output'
Write-Host "Reward file: $($reward[0].FullName)"
Get-Content -LiteralPath $reward[0].FullName
$checks=Get-Content -Raw -LiteralPath (Join-Path $reward[0].DirectoryName 'checks.json') | ConvertFrom-Json
$checks.checks | ConvertTo-Json
if ($null -ne $checks.behaviour_result) { $checks.behaviour_result | ConvertTo-Json }
Write-Host "Harbor version:" -ForegroundColor Cyan
wsl -d Ubuntu -- bash -lc 'harbor --version'
Write-Host 'Read-only evidence display complete.' -ForegroundColor Green
