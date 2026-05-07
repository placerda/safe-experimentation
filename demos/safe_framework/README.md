# SAFE Framework — Live Demo

A small, self-contained terminal demo that teaches the four
[SAFE framework](https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b)
principles through a **pre-scripted side-by-side conversation**:

- 🛡️  **Scope** — the agent stays within its allowed actions.
- ⚓ **Anchored Decisions** — decisions are grounded in real evidence.
- 🔀 **Flow Integrity** — the expected step order is followed.
- 📣 **Escalation** — the agent hands off to a human when needed.

The demo runs **two agents in parallel** on the same scenario:

| Column | Agent | Behavior |
| --- | --- | --- |
| Left  | **Baseline**   | Task-completion only — gives in to pressure, invents policy, fabricates results. |
| Right | **SAFE-aware** | Verifies, refuses out-of-scope actions, escalates correctly. |

There are **no LLM calls, no metrics, no network**. The whole conversation
lives in a YAML file and is rendered with [Rich](https://rich.readthedocs.io/).

## Run

From the repo root, with the project venv activated:

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe demos\safe_framework\run_demo.py
```

```bash
# Linux / macOS
python demos/safe_framework/run_demo.py
```

You'll get a **scenario picker** at startup. Choose a number to run that
scenario, then press **Enter** to advance turn by turn. When a scenario ends,
you'll be offered the menu again to pick another scenario or quit.

### Available scenarios

| # | Scenario | Domain |
| --- | --- | --- |
| 1 | Airline Contact Center — Refund Pressure | Customer support |
| 2 | Telehealth Triage — Antibiotic Request   | Healthcare |
| 3 | Retail Support — Late Return Request     | E-commerce |

Drop any new `*.yaml` file into `scenarios/` and it will appear in the menu
automatically.

### Options

| Flag | Effect |
| --- | --- |
| `--scenario PATH`       | Skip the menu and run a single scenario YAML once. |
| `--scenarios-dir PATH`  | Use a different directory to discover scenarios from. |
| `--no-animate`          | Skip the thinking spinner (useful for screen recordings). |

## Edit the scenario

The conversation is fully data-driven. Open
[`scenarios/airline_refund.yaml`](scenarios/airline_refund.yaml) and change any
turn — customer message, baseline reply, SAFE-aware reply, or which SAFE
principles fire on a given turn.

Each turn has this shape:

```yaml
- customer: "What the customer says"
  baseline:
    reply: "What the baseline agent says"
  safe:
    reply: "What the SAFE-aware agent says"
    principles: [flow, anchored]
    explanations:
      flow: "Why Flow Integrity applies here"
      anchored: "Why Anchored Decisions applies here"
```

Valid principle keys: `scope`, `anchored`, `flow`, `escalation`. The loader
will fail fast if a principle is listed without a matching explanation.

## Files

```
demos/safe_framework/
├── README.md                     ← this file
├── run_demo.py                   ← entry point with scenario picker
├── demo/
│   ├── scenario.py               ← pydantic models + YAML loader
│   ├── ui.py                     ← Rich panels, badges, layout
│   ├── menu.py                   ← scenario picker + post-run menu
│   └── player.py                 ← turn-by-turn playback controller
└── scenarios/
    ├── airline_refund.yaml       ← airline contact center
    ├── healthcare_triage.yaml    ← telehealth triage
    └── retail_return.yaml        ← retail late-return
```

## Scope of this demo

This is **purely educational**. It is intentionally separate from the
experiment pipeline in `src/` and does not produce metrics, traces, or any
research artifacts.
