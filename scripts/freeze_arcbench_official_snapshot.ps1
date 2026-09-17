param(
    [string]$ApiBase = "https://arc-bench.com/api",
    [string]$SnapshotParent = "workstreams/arc-bench/official-snapshots"
)

$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue), $Content, $encoding)
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $json = $Value | ConvertTo-Json -Depth 40
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $json + "`n", $encoding)
}

function Get-ApiJson {
    param([Parameter(Mandatory = $true)][string]$Path)
    $url = "$ApiBase$Path"
    $lastError = $null
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        try {
            return Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 90 -Headers @{ Accept = "application/json" }
        }
        catch {
            $lastError = $_.Exception.Message
            if ($attempt -lt 2) {
                Start-Sleep -Seconds 1
            }
        }
    }
    throw "GET $url failed after 2 attempts: $lastError"
}

function Get-ApiFile {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $lastError = $null
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 90 -OutFile $Path | Out-Null
            return
        }
        catch {
            $lastError = $_.Exception.Message
            if ($attempt -lt 2) {
                Start-Sleep -Seconds 1
            }
        }
    }
    throw "GET $Url failed after 2 attempts: $lastError"
}

function Assert-SafeRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    if ([System.IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains(":") -or $RelativePath.Split('/') -contains ".." -or $RelativePath.Split('\') -contains "..") {
        throw "Unsafe relative path from official API: $RelativePath"
    }
}

function Join-AssetUrl {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )
    $parts = $Base.Split("?", 2)
    $url = "$($parts[0].TrimEnd('/'))/$RelativePath"
    if ($parts.Count -eq 2 -and $parts[1]) {
        $url += "?$($parts[1])"
    }
    return $url.Replace("http://arc-bench.com", "https://arc-bench.com")
}

function Find-LocalRequirement {
    param([Parameter(Mandatory = $true)][string]$RequirementId)
    $leaf = ($RequirementId -split "--")[-1]
    $candidates = @(
        "arc/tasks/$RequirementId/requirements.yaml",
        "arc/tasks/$($RequirementId.Replace('--', '/'))/requirements.yaml",
        "arc/tasks/$leaf/requirements.yaml"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    $matches = Get-ChildItem -LiteralPath "arc/tasks" -Recurse -File -Filter "requirements.yaml" -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -like "*$leaf*" }
    if ($matches.Count -eq 1) {
        return $matches[0].FullName
    }
    return $null
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

$snapshotId = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss'Z'")
$snapshotRoot = Join-Path (Get-Location) "$SnapshotParent/$snapshotId"
New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null

$competitionIds = @(
    "arc-bench-web",
    "smoke-evolution",
    "smoke",
    "ticket-booking-evolution",
    "ticket-booking",
    "arc-bench-lite"
)

$manifest = [ordered]@{
    schema_version = 1
    snapshot_id = $snapshotId
    captured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    source = [ordered]@{
        api_base = $ApiBase
        catalog = "competition"
        authority = "ARC-Bench public competition API"
        hidden_tests = $false
    }
    repository = [ordered]@{
        git_head = (& git rev-parse HEAD).Trim()
        git_branch = (& git branch --show-current).Trim()
    }
    competitions = @()
    tasks = @()
    files = @()
    errors = @()
}

foreach ($competitionId in $competitionIds) {
    try {
        $competition = Get-ApiJson "/competitions/$competitionId"
        $competitionDir = Join-Path $snapshotRoot "competitions/$competitionId"
        New-Item -ItemType Directory -Force -Path $competitionDir | Out-Null
        $competitionJsonPath = Join-Path $competitionDir "competition.json"
        $encoding = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($competitionJsonPath, ($competition | ConvertTo-Json -Depth 40) + "`n", $encoding)

        $manifest.competitions += [ordered]@{
            id = $competition.id
            title = $competition.title
            status = $competition.status
            task_count = $competition.task_count
            total_tests = $competition.total_tests
            template_required = $competition.template_required
            template_source_competition_id = $competition.template_source_competition_id
            task_ids = @($competition.tasks | ForEach-Object { $_.id })
        }

        foreach ($task in @($competition.tasks)) {
            $taskId = [string]$task.id
            $taskDir = Join-Path $competitionDir "tasks/$taskId"
            $taskReqDir = Join-Path $taskDir "requirements"
            $taskTestsDir = Join-Path $taskDir "public-tests"
            $taskReferencesDir = Join-Path $taskDir "references"
            New-Item -ItemType Directory -Force -Path $taskReqDir, $taskTestsDir, $taskReferencesDir | Out-Null

            $requirement = Get-ApiJson "/requirements/$([Uri]::EscapeDataString($taskId))?catalog=competition"
            $taskJsonPath = Join-Path $taskDir "task.json"
            [System.IO.File]::WriteAllText($taskJsonPath, ($requirement | ConvertTo-Json -Depth 40) + "`n", $encoding)
            [System.IO.File]::WriteAllText((Join-Path $taskReqDir "requirements.yaml"), [string]$requirement.requirements_yaml, $encoding)
            [System.IO.File]::WriteAllText((Join-Path $taskReqDir "requirements.md"), [string]$requirement.requirements_markdown, $encoding)
            if ($null -ne $requirement.prerequisites_markdown) {
                [System.IO.File]::WriteAllText((Join-Path $taskReqDir "prerequisites.md"), [string]$requirement.prerequisites_markdown, $encoding)
            }

            $tests = Get-ApiJson "/requirements/$([Uri]::EscapeDataString($taskId))/tests?catalog=competition"
            $testIndex = [ordered]@{
                task_id = $taskId
                file_count = @($tests.files).Count
                paths = @($tests.files | ForEach-Object { $_.path })
                public_downloads = $tests.public_downloads
            }
            [System.IO.File]::WriteAllText((Join-Path $taskTestsDir "index.json"), ($testIndex | ConvertTo-Json -Depth 20) + "`n", $encoding)
            foreach ($testFile in @($tests.files)) {
                $relativeTestPath = [string]$testFile.path
                Assert-SafeRelativePath $relativeTestPath
                $testPath = Join-Path $taskTestsDir ($relativeTestPath.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
                $testParent = Split-Path -Parent $testPath
                New-Item -ItemType Directory -Force -Path $testParent | Out-Null
                [System.IO.File]::WriteAllText($testPath, [string]$testFile.content, $encoding)
            }

            $allRequirementText = "$( [string]$requirement.requirements_yaml )`n$( [string]$requirement.requirements_markdown )"
            $assetMatches = [regex]::Matches($allRequirementText, '(?i)(?:\./)?(?<kind>reference|assets)/(?<path>[^\s\)\"''<>]+\.(?:png|jpe?g|gif|webp|svg|bmp|ico|avif))')
            $assets = @{}
            foreach ($match in $assetMatches) {
                $kind = $match.Groups['kind'].Value.ToLowerInvariant()
                $relativeAssetPath = $match.Groups['path'].Value
                $key = "$kind/$relativeAssetPath"
                $assets[$key] = [ordered]@{ kind = $kind; path = $relativeAssetPath }
            }
            $assetRecords = @()
            foreach ($asset in $assets.Values) {
                Assert-SafeRelativePath $asset.path
                $base = [string]$requirement.references_base_url
                if ($asset.kind -eq "assets") {
                    $base = [string]$requirement.assets_base_url
                }
                if ([string]::IsNullOrWhiteSpace($base)) {
                    $base = [string]$task.references_base_url
                    if ($asset.kind -eq "assets") {
                        $base = [string]$task.assets_base_url
                    }
                }
                if ([string]::IsNullOrWhiteSpace($base)) {
                    $manifest.errors += "No $($asset.kind) base URL for $taskId/$($asset.path)"
                    continue
                }
                $assetUrl = Join-AssetUrl -Base $base -RelativePath $asset.path
                $assetParent = $taskReferencesDir
                if ($asset.kind -eq "assets") {
                    $assetParent = Join-Path $taskDir "assets"
                }
                $assetPath = Join-Path $assetParent ($asset.path.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
                try {
                    Get-ApiFile -Url $assetUrl -Path $assetPath
                    $assetRecords += [ordered]@{
                        status = "downloaded"
                        kind = $asset.kind
                        path = $asset.path
                        source_url = $assetUrl
                        local_path = (Resolve-Path -LiteralPath $assetPath).Path.Substring((Get-Location).Path.Length + 1)
                        bytes = (Get-Item -LiteralPath $assetPath).Length
                        sha256 = Get-Sha256 $assetPath
                    }
                }
                catch {
                    $assetError = $_.Exception.Message
                    $assetStatus = "download_failed"
                    if ($assetError -match "404|Not Found") {
                        $assetStatus = "missing_official"
                    }
                    $assetRecords += [ordered]@{
                        status = $assetStatus
                        kind = $asset.kind
                        path = $asset.path
                        source_url = $assetUrl
                        error = $assetError
                    }
                    if ($assetStatus -ne "missing_official") {
                        $manifest.errors += "Asset download failed for $taskId/$($asset.path): $assetError"
                    }
                }
            }
            $assetJson = "[]`n"
            if ($assetRecords.Count -gt 0) {
                $assetJson = ($assetRecords | ConvertTo-Json -Depth 20) + "`n"
            }
            [System.IO.File]::WriteAllText((Join-Path $taskDir "assets.json"), $assetJson, $encoding)

            $localRequirementPath = Find-LocalRequirement $taskId
            $localRequirementSha = $null
            if ($localRequirementPath) {
                $localRequirementSha = Get-Sha256 $localRequirementPath
            }
            $officialRequirementPath = Join-Path $taskReqDir "requirements.yaml"
            $manifest.tasks += [ordered]@{
                id = $taskId
                competition_id = $competitionId
                title = $task.title
                total_tests = $task.total_tests
                module_count = $task.module_count
                downloaded_test_files = @($tests.files).Count
                downloaded_assets = @($assetRecords | Where-Object status -eq "downloaded").Count
                missing_official_assets = @($assetRecords | Where-Object status -eq "missing_official").Count
                official_requirement_sha256 = Get-Sha256 $officialRequirementPath
                local_requirement_path = $localRequirementPath
                local_requirement_sha256 = $localRequirementSha
                local_requirement_matches = ($null -ne $localRequirementSha -and $localRequirementSha -eq (Get-Sha256 $officialRequirementPath))
            }
        }
    }
    catch {
        $manifest.errors += "Competition $competitionId failed: $($_.Exception.Message)"
    }
}

$allFiles = Get-ChildItem -LiteralPath $snapshotRoot -Recurse -File | Where-Object { $_.Name -ne "manifest.json" }
foreach ($file in $allFiles) {
    $relative = $file.FullName.Substring($snapshotRoot.Length + 1).Replace('\', '/')
    $manifest.files += [ordered]@{
        path = $relative
        bytes = $file.Length
        sha256 = Get-Sha256 $file.FullName
    }
}

$manifestPath = Join-Path $snapshotRoot "manifest.json"
[System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 40) + "`n", $encoding)

$summary = [ordered]@{
    snapshot_id = $snapshotId
    snapshot_path = $snapshotRoot
    competitions = @($manifest.competitions).Count
    tasks = @($manifest.tasks).Count
    files = @($manifest.files).Count
    errors = @($manifest.errors).Count
    local_requirement_matches = @($manifest.tasks | Where-Object local_requirement_matches).Count
}
$summary | ConvertTo-Json -Depth 10
if ($manifest.errors.Count -gt 0) {
    Write-Error "Snapshot completed with $($manifest.errors.Count) recorded errors. Inspect manifest.json."
    exit 2
}
