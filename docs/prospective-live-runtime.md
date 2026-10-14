# Frozen prospective live runtime

The generated live runtime consumes the committed hidden suite and run plan
without adding oracle fields to agent messages. It provides deterministic
per-task tools/backend state, scripted manifest confirmation, the three frozen
arms, incremental `AgentTrace` persistence, and one infrastructure-only retry.
Completed jobs are never rerun on resume. A stale running attempt is preserved
as `process_crash`; model refusal, tool failure, guard blocking, turn
exhaustion, and oracle failure remain outcomes.

No-cost full-plan smoke run:

```powershell
python scripts\run_prospective_live.py --mode smoke `
  --output outputs\prospective-study-smoke
```

Paid Azure OpenAI run (set the existing `AZURE_OPENAI_*` environment values):

```powershell
python scripts\run_prospective_live.py --mode paid `
  --output outputs\prospective-study
```

Both commands are resume-safe and always consume the complete 24-task,
two-seed, three-arm frozen plan. Analyze only after all 144 rows are complete.
