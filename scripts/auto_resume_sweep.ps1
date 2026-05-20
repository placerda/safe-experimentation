# auto_resume_sweep.ps1
# Self-resuming wrapper for the OpenRouter SAFE sweep.
# Loops until results.json appears, resuming after each crash.

$Root        = "c:\Users\kmanchikanti\Desktop\code\safe-experimentation.worktrees\agents-repo-overview-explanation"
$RunDir      = "$Root\outputs\runs\20260519_153121__llama3.3-70b"
$Config      = "configs\experiment.openrouter.yaml"
$LogFile     = "$RunDir\sweep_runner.log"
$ResultsFile = "$RunDir\results.json"

Set-Location $Root

function Log([string]$msg) {
    $ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

Log "Auto-resume wrapper started. PID: $PID"

$attempt = 0
while (-not (Test-Path $ResultsFile)) {
    $attempt++
    $traceCount = (Get-ChildItem "$RunDir\traces" -Filter "*.json" -ErrorAction SilentlyContinue).Count
    Log "Attempt $attempt - $traceCount/720 traces done. Launching run_experiment.py..."

    $stdOut = "$RunDir\stdout_$attempt.log"
    $stdErr = "$RunDir\stderr_$attempt.log"
    $args   = "scripts\run_experiment.py --config $Config --resume-dir `"$RunDir`""

    $procArgs = @{
        FilePath               = "python"
        ArgumentList           = $args
        WorkingDirectory       = $Root
        NoNewWindow            = $true
        PassThru               = $true
        RedirectStandardOutput = $stdOut
        RedirectStandardError  = $stdErr
    }
    $proc = Start-Process @procArgs
    Log "  Child PID: $($proc.Id)"
    $proc.WaitForExit()
    Log "  Exited with code: $($proc.ExitCode)"

    if (Test-Path $ResultsFile) {
        Log "results.json found - sweep complete!"
        break
    }

    $traceCount2 = (Get-ChildItem "$RunDir\traces" -Filter "*.json" -ErrorAction SilentlyContinue).Count
    Log "  Traces after exit: $traceCount2/720. Waiting 15s before retry..."
    Start-Sleep -Seconds 15
}

Log "Wrapper done."
