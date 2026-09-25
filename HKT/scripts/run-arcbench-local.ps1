param(
    [switch]$Check,
    [switch]$Grade,
    [string]$Task = "smoke--counter",
    [string]$Name = "try1",
    [int]$Port = 43100,
    [int]$SmokePort = 43101,
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

# Fill in your ARC-Bench key before starting a task.
$env:ARCBENCH_API_KEY = "ak_EfW5PaYK17X7uduJBxIaj9kuVO_eBSC9T6v0jdXxSCU"
$env:OPENAI_BASE_URL = "https://api.arc-bench.com/v1"
$env:MODEL = "deepseek-v4-flash"
$env:OCTOS_BIN = "D:\items\Hackathon\octos-p\target\release\octos.exe"

$Repo = "D:\items\Hackathon\octos-p"
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Runner = Join-Path $Repo "arc\run-task-local.py"
$Grader = Join-Path $Repo "arc\grade-local.py"
$TaskDir = Join-Path $Repo "arc\tasks\$Task"

if ($env:ARCBENCH_API_KEY -eq "PASTE_YOUR_ARCBENCH_API_KEY_HERE") {
    throw "Please set ARCBENCH_API_KEY in this script before running it."
}

foreach ($Path in @($Python, $Runner, $env:OCTOS_BIN, (Join-Path $TaskDir "requirements.yaml"))) {
    if (-not (Test-Path $Path -PathType Leaf)) {
        throw "Required file not found: $Path"
    }
}

if ($Grade) {
    if ([string]::IsNullOrWhiteSpace($OutputDir)) {
        throw "-OutputDir is required with -Grade."
    }
    & $Python $Grader $OutputDir $Task $Port
    exit $LASTEXITCODE
}

$RunnerArgs = @($Runner, $TaskDir, "--port", $Port, "--smoke-port", $SmokePort)
if ($Check) {
    $RunnerArgs += "--check"
} else {
    $RunnerArgs += @("--name", $Name)
}

& $Python @RunnerArgs
exit $LASTEXITCODE
