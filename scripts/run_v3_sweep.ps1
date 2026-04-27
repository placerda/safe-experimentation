# v3 sweep driver — runs the 3 chunks sequentially with logs.
# Usage: pwsh scripts\run_v3_sweep.ps1
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1
$env:AZURE_OPENAI_ENDPOINT = "https://aif-paulolacerda-0426261026.openai.azure.com/"
$env:AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4.1"
$env:AZURE_OPENAI_USER_DEPLOYMENT = "gpt-4.1"
# Pin tenant to avoid DefaultAzureCredential picking up a stale token for a
# different tenant from the AzureCliCredential / shared cache.
$env:AZURE_TENANT_ID = "85fbd7d4-c974-44b3-8f11-47bc1d72ee5b"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = "outputs\sweep_logs\v3_$ts.log"
"=== v3 sweep starting at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
"AZURE_TENANT_ID = $env:AZURE_TENANT_ID" | Tee-Object -FilePath $log -Append
"--- Chunk A: airline+retail extra seeds 1,2 for baseline+safe-aware ---" | Tee-Object -FilePath $log -Append
python scripts\run_experiment.py --domains airline,retail --variants baseline,safe-aware --seeds 1,2 --run-tag v3-extra-seeds 2>&1 | Tee-Object -FilePath $log -Append
"--- Chunk B: airline+retail ablation arms (prompt-only + binding-only) seeds 0,1,2 ---" | Tee-Object -FilePath $log -Append
python scripts\run_experiment.py --domains airline,retail --variants prompt-only,binding-only --seeds 0,1,2 --run-tag v3-ablation 2>&1 | Tee-Object -FilePath $log -Append
"--- Chunk C: telecom all 4 arms seed 0 ---" | Tee-Object -FilePath $log -Append
python scripts\run_experiment.py --domains telecom --seeds 0 --run-tag v3-telecom 2>&1 | Tee-Object -FilePath $log -Append
"=== v3 sweep done at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
