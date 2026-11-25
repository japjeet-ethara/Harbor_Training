# Runs each cheat in attack/cheatN/ through Harbor on a throwaway copy of the
# target task, and saves the reward.json proof into attack/results/.
# Never edits the target's tests/, task.toml or environment/ (only solution/).
$ErrorActionPreference = 'Stop'
$attack = $PSScriptRoot
$target = Join-Path $attack 'target'
$results = Join-Path $attack 'results'
$jobs = Join-Path $env:TEMP 'gunjit-attack-jobs'
$harbor = 'C:\Users\admin\.local\bin\harbor.exe'
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'
New-Item -ItemType Directory -Force $results, $jobs | Out-Null

# Build visible.tsv for cheat3 from the target's visible data (input<TAB>expected).
$vin = Get-Content (Join-Path $target 'tests\data\inputs.txt')
$vex = Get-Content (Join-Path $target 'tests\data\expected.txt')
$tsv = for ($i = 0; $i -lt $vin.Count; $i++) { "$($vin[$i])`t$($vex[$i])" }
[IO.File]::WriteAllText((Join-Path $attack 'cheat3\visible.tsv'), ($tsv -join "`n"), (New-Object Text.UTF8Encoding($false)))

function Run-Cheat($n) {
    $name = "cheat$n"
    $scratch = Join-Path $env:TEMP "gunjit-$name"
    if (Test-Path $scratch) { Remove-Item -Recurse -Force $scratch }
    Copy-Item -Recurse $target $scratch
    # Replace ONLY solution/ with the cheat.
    Remove-Item -Recurse -Force (Join-Path $scratch 'solution')
    New-Item -ItemType Directory (Join-Path $scratch 'solution') | Out-Null
    Get-ChildItem (Join-Path $attack $name) -File | Copy-Item -Destination (Join-Path $scratch 'solution')
    # Restore LF on every .sh under the scratch copy. Git autocrlf=true stored the
    # target's files as LF; the Windows checkout added CRLF, which breaks the bash
    # shebang. Stripping \r reproduces the target's committed bytes (no task change).
    # Restore LF on .sh AND tests/data/*.txt. autocrlf=true stored the target's
    # files as LF; the Windows checkout added CRLF, which breaks the bash shebang
    # and makes the byte-exact answer comparison fail. Stripping \r reproduces the
    # target's committed bytes (its real task), it is not a task change.
    Get-ChildItem $scratch -Recurse -Include *.sh, *.txt | ForEach-Object {
        [IO.File]::WriteAllText($_.FullName, ([IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"), (New-Object Text.UTF8Encoding($false)))
    }

    $jobName = "$name-$(Get-Date -Format yyyyMMdd-HHmmss)"
    & $harbor run -p $scratch -a oracle -o $jobs --job-name $jobName 2>&1 | Out-Host
    $reward = Get-ChildItem (Join-Path $jobs $jobName) -Recurse -Filter reward.json | Select-Object -First 1
    if (-not $reward) { throw "$name produced no reward.json" }
    Copy-Item $reward.FullName (Join-Path $results "$name-reward.json")
    "{0,-7} job={1}  {2}" -f $name, $jobName, ((Get-Content $reward.FullName -Raw) -replace '\s+', ' ')
    Remove-Item -Recurse -Force $scratch
}

1..5 | ForEach-Object { Run-Cheat $_ }
"jobs saved under: $jobs"
