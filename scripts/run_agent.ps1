param(
    [string]$Query = "latest UI UX trends 2026",
    [string]$VaultDir = "Vault",
    [string]$Model = "qwen3.5:4b",
    [int]$MaxResults = 5,
    [int]$ScheduleMinutes = 0
)

$python = Join-Path $PSScriptRoot "..\\venv\\Scripts\\python.exe"
$main = Join-Path $PSScriptRoot "..\\main.py"

& $python $main --query $Query --vault-dir $VaultDir --model $Model --max-results $MaxResults --schedule-minutes $ScheduleMinutes
