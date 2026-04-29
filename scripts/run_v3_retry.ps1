$ErrorActionPreference = "Continue"
Set-Location "C:\Users\paulolacerda\workspace\safe-experimentation"
. .\.venv\Scripts\Activate.ps1
$env:AZURE_OPENAI_ENDPOINT = "https://aif-amth4qdo24te2.cognitiveservices.azure.com/"
$env:AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4.1"
$env:AZURE_OPENAI_USER_DEPLOYMENT = "gpt-4.1"
$env:AZURE_TENANT_ID = "85fbd7d4-c974-44b3-8f11-47bc1d72ee5b"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = "outputs\sweep_logs\retry_$ts.log"
"=== retry starting at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
python scripts\retry_failed.py outputs\runs\20260427_200216__v3-extra-seeds outputs\runs\20260428_095513__v3-ablation outputs\runs\20260428_163342__v3-telecom 2>&1 | Tee-Object -FilePath $log -Append
"=== retry done at $(Get-Date) ===" | Tee-Object -FilePath $log -Append
