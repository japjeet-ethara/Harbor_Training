param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('A', 'B', 'Echo')]
    [string]$Variant
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$solve = Join-Path $repo 'solution\solve.sh'
$src = Join-Path $repo ("cheat\{0}\solve.sh" -f $Variant.ToLower())
if (-not (Test-Path $src)) {
    throw "missing cheat variant: $src"
}

$backup = Join-Path $env:TEMP ("titlecase-solve-{0}.bak" -f [guid]::NewGuid().ToString('n'))
Copy-Item -LiteralPath $solve -Destination $backup -Force
$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
$taskParent = Split-Path $repo -Parent
Push-Location $taskParent
try {
    Copy-Item -LiteralPath $src -Destination $solve -Force
    & harbor run -p ./titlecase-go -a oracle -y
    if ($LASTEXITCODE -ne 0) {
        throw "harbor run failed with exit $LASTEXITCODE"
    }
    $job = Get-ChildItem -LiteralPath (Join-Path (Get-Location) 'jobs') -Directory |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    $reward = Get-ChildItem -LiteralPath $job.FullName -Recurse -Filter reward.json |
        Where-Object { $_.Directory.Name -eq 'verifier' } |
        Select-Object -First 1
    $details = Get-ChildItem -LiteralPath $job.FullName -Recurse -Filter reward-details.json |
        Where-Object { $_.Directory.Name -eq 'verifier' } |
        Select-Object -First 1
    Write-Output "VARIANT $Variant"
    Write-Output "JOB $($job.FullName)"
    Write-Output '--- reward.json ---'
    Get-Content -LiteralPath $reward.FullName -Raw
    Write-Output '--- reward-details.json ---'
    Get-Content -LiteralPath $details.FullName -Raw
}
finally {
    Copy-Item -LiteralPath $backup -Destination $solve -Force
    Remove-Item -LiteralPath $backup -Force
    Pop-Location
}
