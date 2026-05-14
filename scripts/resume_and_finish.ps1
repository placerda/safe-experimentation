# Resume seed-2 (in existing dir), run seed-3, then regenerate analysis.
# Designed to be launched detached so it survives session shutdown.

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1

$env:AZURE_OPENAI_ENDPOINT        = "https://aif-safe-experimentation.cognitiveservices.azure.com/"
$env:AZURE_OPENAI_API_VERSION     = "2024-10-21"
$env:AZURE_OPENAI_DEPLOYMENT      = "gpt-4.1"
$env:AZURE_OPENAI_USER_DEPLOYMENT = "gpt-4.1"
$env:AZURE_TENANT_ID              = "16b3c013-d300-468d-ac64-7eda0820b6d3"

$seed2Dir = "outputs\runs\20260514_011035__v4-seed2"
$logTs    = Get-Date -Format "yyyyMMdd_HHmmss"
$log      = "outputs\sweep_logs\v4_resume_$logTs.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

"=== resume_and_finish starting at $(Get-Date) ===" | Tee-Object -FilePath $log -Append

"--- Resuming seed-2 into $seed2Dir ---" | Tee-Object -FilePath $log -Append
python scripts\run_experiment.py `
    --config configs/experiment.v4.yaml `
    --domains airline,retail `
    --seeds 2 `
    --resume-dir $seed2Dir 2>&1 | Tee-Object -FilePath $log -Append

"--- Running seed-3 (fresh) ---" | Tee-Object -FilePath $log -Append
python scripts\run_experiment.py `
    --config configs/experiment.v4.yaml `
    --domains airline,retail `
    --seeds 3 `
    --run-tag v4-seed3 2>&1 | Tee-Object -FilePath $log -Append

"--- Identifying run dirs for analysis ---" | Tee-Object -FilePath $log -Append
$seed1Dir = "outputs\runs\20260513_203156__v4-seed1"
$seed3Dir = (Get-ChildItem outputs\runs -Directory -Filter "*__v4-seed3" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
"Seed1: $seed1Dir" | Tee-Object -FilePath $log -Append
"Seed2: $seed2Dir" | Tee-Object -FilePath $log -Append
"Seed3: $seed3Dir" | Tee-Object -FilePath $log -Append

"--- Running analyze_v4.py ---" | Tee-Object -FilePath $log -Append
python scripts\analyze_v4.py $seed1Dir $seed2Dir $seed3Dir 2>&1 | Tee-Object -FilePath $log -Append

"--- Running render_v4_tables.py ---" | Tee-Object -FilePath $log -Append
python scripts\render_v4_tables.py 2>&1 | Tee-Object -FilePath $log -Append

"=== resume_and_finish done at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
"Log: $log"
