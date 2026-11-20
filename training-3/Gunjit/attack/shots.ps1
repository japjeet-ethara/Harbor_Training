# Screenshot each Harbor viewer job page (proof of every attack/reference run).
param([int]$Port = 8093)
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$out = Join-Path $PSScriptRoot 'screenshots'
$jobs = Join-Path $env:TEMP 'gunjit-attack-jobs'
New-Item -ItemType Directory -Force $out | Out-Null
foreach ($job in Get-ChildItem $jobs -Directory) {
    $label = ($job.Name -split '-\d{8}-')[0]   # cheat1, oracle, his, ...
    $file = Join-Path $out "$label.png"
    $profile = Join-Path $env:TEMP "edge-shot-$label"
    $args = @('--headless=new', '--disable-gpu', '--hide-scrollbars', "--user-data-dir=$profile",
        '--window-size=2000,640', '--virtual-time-budget=9000', "--screenshot=$file",
        "http://127.0.0.1:$Port/jobs/$($job.Name)")
    Start-Process -FilePath $edge -ArgumentList $args -Wait -WindowStyle Hidden
    Remove-Item -Recurse -Force $profile -ErrorAction SilentlyContinue
    "$label.png: $((Get-Item $file -ErrorAction SilentlyContinue).Length) bytes"
}
