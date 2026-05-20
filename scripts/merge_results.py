"""Merge all per-model results.json files into a single combined_results.json.

Each source file contributes all its rows unchanged; a `run_id` column is added
to identify the originating run directory.  Rows from older runs that lack a
`seed` field get seed=0 filled in for consistency.

Output: outputs/reports/combined_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Canonical runs to include, in chronological order.
# (run_dir, display_model) — display_model overrides the model field so rows
# from runs that were tagged with the wrong model name are corrected.
# Note: grok-3/grok-3-mini runs (20260519_152221) were executed before the
# provider-tagging fix and are labelled "meta-llama/..." in the JSON — we
# override that here to the correct model name.
RUNS: list[tuple[str, str]] = [
    ("outputs/runs/20260426_172556__gpt-4.1",      "gpt-4.1"),
    ("outputs/runs/20260426_172704__gpt-5-mini",   "gpt-5-mini"),
    ("outputs/runs/20260519_152221__grok-3",       "grok-3"),
    ("outputs/runs/20260519_152221__grok-3-mini",  "grok-3-mini"),
    ("outputs/runs/20260519_153121__llama3.3-70b", "meta-llama/llama-3.3-70b-instruct"),
]


def main() -> None:
    combined: list[dict] = []

    for run_rel, display_model in RUNS:
        results_path = ROOT / run_rel / "results.json"
        if not results_path.exists():
            print(f"SKIP (no results.json): {run_rel}")
            continue

        rows = json.loads(results_path.read_text(encoding="utf-8"))
        run_id = Path(run_rel).name
        added = 0
        for row in rows:
            # Always use the authoritative display_model (overrides any wrong label
            # recorded during the run, e.g. grok runs that were mis-tagged as llama).
            row["model"] = display_model
            # Back-fill seed for old runs
            if "seed" not in row:
                row["seed"] = 0
            # Tag with run provenance
            row["run_id"] = run_id
            combined.append(row)
            added += 1

        print(f"  {run_id}: {added} rows  model={display_model}")

    out_path = ROOT / "outputs" / "reports" / "combined_results.json"
    out_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"\nWrote {len(combined)} rows → {out_path.relative_to(ROOT)}")

    # Print quick summary table
    from collections import defaultdict
    import statistics

    # group by (model, agent_variant, domain)
    groups: dict[tuple, list[float]] = defaultdict(list)
    for row in combined:
        key = (row["model"], row["agent_variant"], row["domain"])
        if row.get("safe_overall") is not None:
            groups[key].append(row["safe_overall"])

    print("\nModel                                  Variant          Domain    n   SAFE")
    print("-" * 82)
    prev_model = None
    for key in sorted(groups):
        model, variant, domain = key
        vals = groups[key]
        if model != prev_model:
            print()
            prev_model = model
        print(f"  {model:<38} {variant:<16} {domain:<9} {len(vals):>3}  {statistics.mean(vals):.3f}")


if __name__ == "__main__":
    main()
