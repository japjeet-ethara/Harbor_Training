[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ResultsRoot = Join-Path $ProjectRoot 'attack\results'
$ReportPath = Join-Path $ResultsRoot 'ALL_CHEAT_RESULTS.md'

function Get-Field {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -ne $property) { return $property.Value }
    return $null
}

function Get-FirstField {
    param($Object, [string[]]$Names)
    foreach ($name in $Names) {
        $value = Get-Field $Object $name
        if ($null -ne $value) { return $value }
    }
    return $null
}

function ConvertTo-ScoreNumber {
    param($Value)
    if ($null -eq $Value -or "$Value" -eq '') { return $null }
    $parsed = 0.0
    if ([double]::TryParse(
        "$Value",
        [Globalization.NumberStyles]::Float,
        [Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )) {
        return $parsed
    }
    return $null
}

function Get-MetricRows {
    param($Result)

    $rows = @()
    $stats = Get-Field $Result 'stats'
    $evals = Get-Field $stats 'evals'
    if ($null -ne $evals) {
        foreach ($evalProperty in $evals.PSObject.Properties) {
            $metrics = Get-Field $evalProperty.Value 'metrics'
            foreach ($metric in @($metrics)) {
                if ($null -ne $metric) { $rows += $metric }
            }
        }
    }

    if ($rows.Count -eq 0) {
        $rows = @(
            (Get-Field (Get-Field $Result 'verifier_result') 'rewards'),
            (Get-Field $Result 'rewards')
        ) | Where-Object { $null -ne $_ }
    }
    if ($rows.Count -eq 0) {
        $metrics = Get-Field $Result 'metrics'
        if ($null -ne $metrics) { $rows = @($metrics) }
    }
    return ,$rows
}

function Get-AverageScore {
    param($MetricRows, [string[]]$Names)
    $values = @()
    foreach ($row in $MetricRows) {
        $number = ConvertTo-ScoreNumber (Get-FirstField $row $Names)
        if ($null -ne $number) { $values += [double]$number }
    }
    if ($values.Count -eq 0) { return $null }
    return (($values | Measure-Object -Average).Average)
}

function Format-Score {
    param($Value)
    if ($null -eq $Value) { return 'N/A' }
    return ([double]$Value).ToString('F3', [Globalization.CultureInfo]::InvariantCulture)
}

function Get-ProjectRelativePath {
    param([string]$Path)
    $rootPath = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\') + '\'
    $fullPath = (Resolve-Path -LiteralPath $Path).Path
    if ($fullPath.StartsWith($rootPath, [StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath.Substring($rootPath.Length)
    }
    return $fullPath
}

function ConvertTo-Date {
    param($Value)
    if ($null -eq $Value -or "$Value" -eq '') { return $null }
    $parsed = [DateTimeOffset]::MinValue
    if ([DateTimeOffset]::TryParse(
        "$Value",
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None,
        [ref]$parsed
    )) {
        return $parsed
    }
    return $null
}

function Get-JobRecord {
    param(
        [int]$CheatNumber,
        [string]$JobDirectory,
        [string]$ResultFile
    )

    $config = $null
    $lock = $null
    $result = $null
    $parseError = $null
    $configFile = Join-Path $JobDirectory 'config.json'
    $lockFile = Join-Path $JobDirectory 'lock.json'

    if (Test-Path -LiteralPath $configFile -PathType Leaf) {
        try { $config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json }
        catch { $parseError = 'Malformed config.json' }
    }
    if (Test-Path -LiteralPath $lockFile -PathType Leaf) {
        try { $lock = Get-Content -LiteralPath $lockFile -Raw | ConvertFrom-Json }
        catch { if (-not $parseError) { $parseError = 'Malformed lock.json' } }
    }
    if ($ResultFile -and (Test-Path -LiteralPath $ResultFile -PathType Leaf)) {
        try { $result = Get-Content -LiteralPath $ResultFile -Raw | ConvertFrom-Json }
        catch { $parseError = 'Malformed job result.json' }
    }

    $jobName = Get-FirstField $config @('job_name', 'name')
    if (-not $jobName) { $jobName = Split-Path -Leaf $JobDirectory }
    $stats = Get-Field $result 'stats'
    $metrics = Get-MetricRows $result

    $total = Get-FirstField $result @('n_total_trials', 'total_trials')
    if ($null -eq $total) { $total = Get-FirstField $stats @('n_total_trials', 'total_trials') }
    if ($null -eq $total) {
        $evals = Get-Field $stats 'evals'
        $evalCounts = @()
        if ($null -ne $evals) {
            foreach ($evalProperty in $evals.PSObject.Properties) {
                $count = ConvertTo-ScoreNumber (Get-Field $evalProperty.Value 'n_trials')
                if ($null -ne $count) { $evalCounts += [int]$count }
            }
        }
        if ($evalCounts.Count -gt 0) { $total = ($evalCounts | Measure-Object -Maximum).Maximum }
    }
    if ($null -eq $total) { $total = 0 }

    $completed = Get-FirstField $stats @('n_completed_trials', 'completed_trials')
    $errored = Get-FirstField $stats @('n_errored_trials', 'n_errors', 'errored_trials')
    $running = Get-FirstField $stats @('n_running_trials', 'running_trials')
    $pending = Get-FirstField $stats @('n_pending_trials', 'pending_trials')
    $cancelled = Get-FirstField $stats @('n_cancelled_trials', 'cancelled_trials')
    if ($null -eq $errored) {
        $evalErrorCount = 0
        $evals = Get-Field $stats 'evals'
        if ($null -ne $evals) {
            foreach ($evalProperty in $evals.PSObject.Properties) {
                $count = ConvertTo-ScoreNumber (Get-Field $evalProperty.Value 'n_errors')
                if ($null -ne $count) { $evalErrorCount += [int]$count }
            }
        }
        $errored = $evalErrorCount
    }
    if ($null -eq $completed) { $completed = 0 }
    if ($null -eq $running) { $running = 0 }
    if ($null -eq $pending) { $pending = 0 }
    if ($null -eq $cancelled) { $cancelled = 0 }

    $finishedAt = ConvertTo-Date (Get-FirstField $result @('finished_at', 'completed_at', 'ended_at'))
    $startedAt = ConvertTo-Date (Get-FirstField $result @('started_at', 'created_at'))
    $lockCreated = ConvertTo-Date (Get-Field $lock 'created_at')
    $jobDate = $finishedAt
    if ($null -eq $jobDate) { $jobDate = $startedAt }
    if ($null -eq $jobDate) { $jobDate = $lockCreated }
    if ($null -eq $jobDate -and $ResultFile) {
        $jobDate = [DateTimeOffset]::new((Get-Item -LiteralPath $ResultFile).LastWriteTime)
    }
    if ($null -eq $jobDate) {
        $jobDate = [DateTimeOffset]::new((Get-Item -LiteralPath $JobDirectory).LastWriteTime)
    }

    $status = 'Incomplete'
    if ($parseError) {
        $status = $parseError
    } elseif ($null -ne $result) {
        $active = ([int]$running -gt 0) -or ([int]$pending -gt 0)
        $countsComplete = ([int]$total -gt 0) -and
            (([int]$completed + [int]$errored + [int]$cancelled) -ge [int]$total)
        if ((($null -ne $finishedAt) -or $countsComplete) -and -not $active) {
            if ([int]$errored -gt 0) { $status = 'Complete (exceptions)' }
            else { $status = 'Complete' }
        } else {
            $status = 'Incomplete'
        }
    }

    $relativeDirectory = Get-ProjectRelativePath $JobDirectory
    $relativeResult = 'N/A'
    if ($ResultFile) {
        $relativeResult = Get-ProjectRelativePath $ResultFile
    }

    return [PSCustomObject]@{
        Cheat = "Cheat $CheatNumber"
        CheatNumber = $CheatNumber
        JobName = [string]$jobName
        TrialCount = if ($null -ne $result) { [string]$total } else { 'N/A' }
        Exceptions = if ($null -ne $result) { [string]$errored } else { 'N/A' }
        BehaviourValue = Get-AverageScore $metrics @('behaviour', 'behavior')
        BuildValue = Get-AverageScore $metrics @('build')
        NoPythonValue = Get-AverageScore $metrics @('no_python', 'noPython', 'noPythonScore')
        RewardValue = Get-AverageScore $metrics @('reward', 'overall_reward', 'overallReward')
        Behaviour = Format-Score (Get-AverageScore $metrics @('behaviour', 'behavior'))
        Build = Format-Score (Get-AverageScore $metrics @('build'))
        NoPython = Format-Score (Get-AverageScore $metrics @('no_python', 'noPython', 'noPythonScore'))
        Reward = Format-Score (Get-AverageScore $metrics @('reward', 'overall_reward', 'overallReward'))
        Status = $status
        SortDate = $jobDate
        Date = $jobDate.ToString('yyyy-MM-dd HH:mm:ss zzz')
        JobDirectory = $relativeDirectory
        ResultPath = $relativeResult
        HasResult = ($null -ne $result)
    }
}

$jobs = @()
$seenDirectories = @{}
for ($cheatNumber = 1; $cheatNumber -le 3; $cheatNumber++) {
    $cheatRoot = Join-Path $ResultsRoot "jobs-cheat$cheatNumber"
    if (-not (Test-Path -LiteralPath $cheatRoot -PathType Container)) { continue }

    # Job folders are the direct children of jobs-cheatN. Trial result files
    # may also be named result.json, but are nested and are intentionally not
    # treated as separate Harbor jobs.
    foreach ($directory in Get-ChildItem -LiteralPath $cheatRoot -Directory -Force) {
        $resultFile = Join-Path $directory.FullName 'result.json'
        $configFile = Join-Path $directory.FullName 'config.json'
        $lockFile = Join-Path $directory.FullName 'lock.json'
        if (-not (Test-Path -LiteralPath $resultFile -PathType Leaf) -and
            -not (Test-Path -LiteralPath $configFile -PathType Leaf) -and
            -not (Test-Path -LiteralPath $lockFile -PathType Leaf)) {
            continue
        }

        $key = [IO.Path]::GetFullPath($directory.FullName).TrimEnd('\').ToLowerInvariant()
        if ($seenDirectories.ContainsKey($key)) { continue }
        $seenDirectories[$key] = $true
        if (-not (Test-Path -LiteralPath $resultFile -PathType Leaf)) { $resultFile = $null }
        $jobs += Get-JobRecord -CheatNumber $cheatNumber -JobDirectory $directory.FullName -ResultFile $resultFile
    }
}

$jobs = @($jobs | Sort-Object SortDate, CheatNumber, JobName)

Write-Host "`nAll Harbor Cheat jobs (oldest first):" -ForegroundColor Cyan
if ($jobs.Count -gt 0) {
    $jobs |
        Select-Object Cheat, JobName, Date, TrialCount, Exceptions, Behaviour, Build,
            @{Name = 'No_Python'; Expression = { $_.NoPython }}, Reward, Status |
        Format-Table -AutoSize -Wrap |
        Out-String -Width 300 |
        Write-Host
} else {
    Write-Host 'No job folders or job-level results found.'
}

$latest = @()
for ($cheatNumber = 1; $cheatNumber -le 3; $cheatNumber++) {
    $completedJobs = @($jobs | Where-Object {
        $_.CheatNumber -eq $cheatNumber -and $_.Status -like 'Complete*'
    } | Sort-Object SortDate -Descending)
    if ($completedJobs.Count -gt 0) {
        $latest += $completedJobs[0]
    } else {
        $latest += [PSCustomObject]@{
            Cheat = "Cheat $cheatNumber"
            CheatNumber = $cheatNumber
            JobName = 'N/A'
            TrialCount = 'N/A'
            Exceptions = 'N/A'
            BehaviourValue = $null
            BuildValue = $null
            NoPythonValue = $null
            RewardValue = $null
            Behaviour = 'N/A'
            Build = 'N/A'
            NoPython = 'N/A'
            Reward = 'N/A'
            Status = 'No completed job'
            SortDate = $null
            Date = 'N/A'
            JobDirectory = 'N/A'
            ResultPath = 'N/A'
            HasResult = $false
        }
    }
}

$rewarded = @($latest | Where-Object { $null -ne $_.RewardValue })
$averageReward = $null
if ($rewarded.Count -eq 3) {
    $averageReward = ($rewarded | Measure-Object -Property RewardValue -Average).Average
}
$atLeastPointTwo = @($rewarded | Where-Object { $_.RewardValue -ge 0.2 }).Count
$perfect = @($rewarded | Where-Object { $_.RewardValue -eq 1.0 }).Count

Write-Host "`nLatest completed job per Cheat:" -ForegroundColor Cyan
$latest |
    Select-Object Cheat, JobName, Date, Behaviour, Build,
        @{Name = 'No_Python'; Expression = { $_.NoPython }}, Reward, Status |
    Format-Table -AutoSize -Wrap
if ($null -ne $averageReward) {
    $averageText = Format-Score $averageReward
} else {
    $averageText = "N/A (completed results for $($rewarded.Count)/3 cheats)"
}
Write-Host "Average latest reward: $averageText"
Write-Host "Latest rewards >= 0.2: $atLeastPointTwo"
Write-Host "Latest rewards = 1.000: $perfect"

$generatedAt = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
$markdown = New-Object System.Collections.Generic.List[string]
$markdown.Add('# Harbor Cheat Results')
$markdown.Add('')
$markdown.Add("Generated: $generatedAt")
$markdown.Add('')
$markdown.Add('## All jobs')
$markdown.Add('')
$markdown.Add('| Cheat | Job name | Date | Trials | Exceptions | Behaviour | Build | No_Python | Reward | Status | Job result path |')
$markdown.Add('|---|---|---|---:|---:|---:|---:|---:|---:|---|---|')
foreach ($job in $jobs) {
    $markdown.Add("| $($job.Cheat) | $($job.JobName) | $($job.Date) | $($job.TrialCount) | $($job.Exceptions) | $($job.Behaviour) | $($job.Build) | $($job.NoPython) | $($job.Reward) | $($job.Status) | ``$($job.ResultPath)`` |")
}
if ($jobs.Count -eq 0) {
    $markdown.Add('| N/A | No Harbor job found | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Missing | N/A |')
}
$markdown.Add('')
$markdown.Add('## Latest completed job per Cheat')
$markdown.Add('')
$markdown.Add('| Cheat | Job name | Date | Behaviour | Build | No_Python | Reward | Status |')
$markdown.Add('|---|---|---|---:|---:|---:|---:|---|')
foreach ($job in $latest) {
    $markdown.Add("| $($job.Cheat) | $($job.JobName) | $($job.Date) | $($job.Behaviour) | $($job.Build) | $($job.NoPython) | $($job.Reward) | $($job.Status) |")
}
$markdown.Add('')
$markdown.Add("Average latest reward: **$averageText**")
$markdown.Add('')
$markdown.Add("Latest rewards >= 0.2: **$atLeastPointTwo**")
$markdown.Add('')
$markdown.Add("Latest rewards = 1.000: **$perfect**")
$markdown.Add('')
$markdown.Add('Incomplete jobs are listed with their available scores; missing scores display as `N/A`. Trial-level result files are excluded.')

New-Item -ItemType Directory -Path $ResultsRoot -Force | Out-Null
Set-Content -LiteralPath $ReportPath -Value $markdown -Encoding UTF8
Write-Host "`nWrote consolidated report: $ReportPath" -ForegroundColor Green
