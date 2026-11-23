param(
    [Parameter(Mandatory=$true)][string]$Jobs,
    [Parameter(Mandatory=$true)][string]$Evidence,
    [Parameter(Mandatory=$true)][string]$Platform
)

$ErrorActionPreference = 'Stop'
$Edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
$Python = "$PWD/work/harbor-venv/Scripts/python.exe"
$Screens = Join-Path $Evidence 'reward-screenshots'
New-Item -ItemType Directory -Path $Screens -Force | Out-Null
(Get-Item -LiteralPath $Edge).VersionInfo.ProductVersion
foreach ($Trial in 'oracle','nop','replay') {
    $HTML = Join-Path $Screens "$Trial.html"
    $PNG = Join-Path $Screens "$Trial.png"
    & $Python work/capture_reward_report.py $Jobs $HTML --job $Trial --host $Platform
    if ($LASTEXITCODE) { throw "Could not prepare the $Trial reward view" }
    $URL = ([uri]$HTML).AbsoluteUri
    $Profile = "$PWD/work/edge-proof-$Trial"
    $Arguments = @(
        '--headless','--disable-gpu','--no-first-run','--disable-extensions',
        '--force-device-scale-factor=1','--window-size=860,510',
        ('--user-data-dir="' + $Profile + '"'),('--screenshot="' + $PNG + '"'),$URL
    )
    $Process = Start-Process -FilePath $Edge -ArgumentList $Arguments -WindowStyle Hidden -Wait -PassThru
    if ($Process.ExitCode -or !(Test-Path -LiteralPath $PNG)) {
        throw "Browser capture failed for $Trial"
    }
    Get-FileHash -Algorithm SHA256 -LiteralPath $PNG
}
