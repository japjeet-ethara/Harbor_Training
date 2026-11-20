# Baseline reference runs on the target task (unchanged tests/), for the ATTACK
# report's context: his real solution (oracle), a do-nothing agent (nop), and his
# own committed cheat. Rewards saved into attack/results/.
$ErrorActionPreference = 'Stop'
$attack = $PSScriptRoot
$target = Join-Path $attack 'target'
$results = Join-Path $attack 'results'
$jobs = Join-Path $env:TEMP 'gunjit-attack-jobs'
$harbor = 'C:\Users\admin\.local\bin\harbor.exe'
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'

function Run-Ref($label, $cheatSolve) {
    $scratch = Join-Path $env:TEMP "gunjit-ref-$label"
    if (Test-Path $scratch) { Remove-Item -Recurse -Force $scratch }
    Copy-Item -Recurse $target $scratch
    if ($cheatSolve) {
        Remove-Item -Recurse -Force (Join-Path $scratch 'solution')
        New-Item -ItemType Directory (Join-Path $scratch 'solution') | Out-Null
        Copy-Item $cheatSolve (Join-Path $scratch 'solution\solve.sh')
    }
    # Restore LF on .sh AND tests/data/*.txt (checkout artifact, see run_attacks.ps1).
    Get-ChildItem $scratch -Recurse -Include *.sh, *.txt | ForEach-Object {
        [IO.File]::WriteAllText($_.FullName, ([IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"), (New-Object Text.UTF8Encoding($false)))
    }
    $agent = if ($label -eq 'nop') { 'nop' } else { 'oracle' }
    $jobName = "$label-$(Get-Date -Format yyyyMMdd-HHmmss)"
    & $harbor run -p $scratch -a $agent -o $jobs --job-name $jobName 2>&1 | Out-Host
    $reward = Get-ChildItem (Join-Path $jobs $jobName) -Recurse -Filter reward.json | Select-Object -First 1
    if ($reward) { Copy-Item $reward.FullName (Join-Path $results "ref-$label-reward.json") }
    $txt = if ($reward) { (Get-Content $reward.FullName -Raw) -replace '\s+', ' ' } else { 'NO REWARD (see job)' }
    "{0,-12} job={1}  {2}" -f $label, $jobName, $txt
    Remove-Item -Recurse -Force $scratch
}

Run-Ref 'oracle' $null                                  # his real Go port
Run-Ref 'nop'    $null                                  # does nothing
Run-Ref 'his-cheat' (Join-Path $target 'cheat\solve.sh')  # his own committed cheat
