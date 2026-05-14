# v4 sweep driver — runs the full pre-registered sweep in 3 chunks (one per seed).
#
# Per protocol.v4.md §3:
#   - 50 airline + 50 retail tasks (selected_tasks/*.jsonl)
#   - 6 variants (baseline, binding, evidence, flow, escalation, all-guardrails)
#   - 3 seeds (1, 2, 3) — same seeds as v3
#   - Total: 1800 cells, ~20h at v3 rate
#
# Usage:
#   pwsh scripts\run_v4_sweep.ps1                 # all 3 seeds sequential
#   pwsh scripts\run_v4_sweep.ps1 -Seeds "1"      # only seed 1
#   pwsh scripts\run_v4_sweep.ps1 -Seeds "2,3"    # seeds 2 and 3
#
# Each chunk lives in its own outputs/runs/<ts>__v4-seed<N> dir.

param(
    [string]$Seeds = "1,2,3"
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1

# Environment — matches the working smoke (.env already has these, but pin
# them explicitly so the sweep driver is self-contained and reproducible).
$env:AZURE_OPENAI_ENDPOINT      = "https://aif-safe-experimentation.cognitiveservices.azure.com/"
$env:AZURE_OPENAI_API_VERSION   = "2024-10-21"
$env:AZURE_OPENAI_DEPLOYMENT    = "gpt-4.1"
$env:AZURE_OPENAI_USER_DEPLOYMENT = "gpt-4.1"
$env:AZURE_TENANT_ID            = "16b3c013-d300-468d-ac64-7eda0820b6d3"

$ts  = Get-Date -Format "yyyyMMdd_HHmmss"
$log = "outputs\sweep_logs\v4_$ts.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

"=== v4 sweep starting at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
"AZURE_TENANT_ID    = $env:AZURE_TENANT_ID"  | Tee-Object -FilePath $log -Append
"AZURE_OPENAI_DEP   = $env:AZURE_OPENAI_DEPLOYMENT" | Tee-Object -FilePath $log -Append
"Seeds requested    = $Seeds" | Tee-Object -FilePath $log -Append

foreach ($s in ($Seeds -split ",")) {
    $s = $s.Trim()
    if (-not $s) { continue }
    $tag = "v4-seed$s"
    "--- Chunk seed $s : 100 tasks × 6 variants (run-tag $tag) ---" | Tee-Object -FilePath $log -Append
    python scripts\run_experiment.py `
        --config configs/experiment.v4.yaml `
        --domains airline,retail `
        --seeds $s `
        --run-tag $tag 2>&1 | Tee-Object -FilePath $log -Append
}

"=== v4 sweep done at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
"Log: $log"
