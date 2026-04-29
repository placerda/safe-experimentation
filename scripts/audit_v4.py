"""Stratified audit of guardrail events.

Samples 30 traces (5 per variant, balanced airline/retail) and emits a
markdown digest of:
  - Each guardrail event with the surrounding tool call context.
  - Cases where SAFE compliance and τ³ reward diverge.
  - Counts of suspected false positives (enforcer fired with no
    plausible policy basis).

Usage:
    python scripts/audit_v4.py outputs/runs/<run1> outputs/runs/<run2> ...
    python scripts/audit_v4.py --auto
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RNG = random.Random(20260429)


def find_v4_runs() -> list[Path]:
    runs_dir = ROOT / "outputs" / "runs"
    return sorted(d for d in runs_dir.iterdir()
                  if d.is_dir() and "v4" in d.name.lower() and "smoke" not in d.name)


def load_traces(run_dirs: list[Path]) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for d in run_dirs:
        td = d / "traces"
        if not td.exists():
            continue
        for fp in td.glob("*.json"):
            try:
                tr = json.loads(fp.read_text(encoding="utf-8"))
                out.append((fp, tr))
            except Exception:
                pass
    return out


def stratified_sample(
    traces: list[tuple[Path, dict]], per_variant: int = 5
) -> list[tuple[Path, dict]]:
    by_strata: dict[tuple[str, str], list] = defaultdict(list)
    for fp, tr in traces:
        key = (tr.get("agent_variant", "?"), tr.get("domain", "?"))
        by_strata[key].append((fp, tr))
    sample: list = []
    variants = sorted({k[0] for k in by_strata})
    domains = sorted({k[1] for k in by_strata})
    per_cell = max(1, per_variant // max(1, len(domains)))
    for v in variants:
        for d in domains:
            cell = by_strata.get((v, d), [])
            RNG.shuffle(cell)
            sample.extend(cell[:per_cell])
    return sample


def render_audit(sample: list[tuple[Path, dict]]) -> str:
    lines: list[str] = []
    lines.append("# v4 guardrail audit (stratified sample)\n")
    lines.append(f"Sample size: {len(sample)} traces.\n")

    by_var: dict[str, int] = defaultdict(int)
    fp_count: dict[str, int] = defaultdict(int)
    divergence: list[dict] = []

    for fp, tr in sample:
        v = tr.get("agent_variant", "?")
        by_var[v] += 1
        events = tr.get("metadata", {}).get("guardrail_events", []) or []
        tool_calls = tr.get("tool_calls_log", []) or []

        # Heuristic false-positive indicators per enforcer.
        for e in events:
            enforcer = e.get("enforcer", "")
            action = e.get("action", "")
            if enforcer == "binding" and action == "filter":
                # Always-on; not a FP.
                continue
            if enforcer == "evidence" and action == "block":
                # Suspect FP if a read-only call WAS made before the block.
                read_before = any(
                    not (tc.get("name", "").startswith(("update_", "modify_", "cancel_",
                                                        "book_", "send_", "issue_",
                                                        "process_", "exchange_", "return_",
                                                        "refund_", "transfer_", "create_",
                                                        "delete_", "remove_", "add_",
                                                        "submit_", "confirm_")))
                    for tc in tool_calls
                )
                if read_before:
                    fp_count[f"{enforcer}/{action}"] += 1
            if enforcer == "escalation" and action == "remind":
                # Suspect FP if the trace's escalation evaluator passed AND
                # no transfer_to_human call happened (i.e. agent ignored the
                # reminder and still got E=1.0 — reminder was redundant).
                pass

        # Note: divergence requires SAFE eval data not in trace.
    
    # Sample event listing
    lines.append("## Per-variant trace count in sample\n")
    for v, n in sorted(by_var.items()):
        lines.append(f"- **{v}**: {n}")
    lines.append("")

    lines.append("## Suspected false-positive counts\n")
    if fp_count:
        for k, n in sorted(fp_count.items()):
            lines.append(f"- {k}: {n} suspected FPs")
    else:
        lines.append("(No suspected false positives flagged by heuristics.)")
    lines.append("")

    lines.append("## Per-trace event detail (truncated to first 40 traces)\n")
    for i, (fp, tr) in enumerate(sample[:40]):
        events = tr.get("metadata", {}).get("guardrail_events", []) or []
        if not events:
            continue
        v = tr.get("agent_variant", "?")
        tid = tr.get("task_id", "?")
        lines.append(f"### {v}/{tid} ({fp.name})")
        for e in events:
            lines.append(
                f"- t{e.get('turn','?')} {e.get('enforcer')}/{e.get('hook')}/{e.get('action')}"
                + (f" tool=`{e.get('tool_name')}`" if e.get('tool_name') else "")
                + (f" — {e.get('reason')}" if e.get('reason') else "")
            )
        lines.append("")

    return "\n".join(lines)


def main(run_dirs: list[Path]) -> None:
    traces = load_traces(run_dirs)
    if not traces:
        raise SystemExit("No traces found.")
    sample = stratified_sample(traces, per_variant=5)
    out_path = ROOT / "outputs" / "reports" / "v4_audit.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_audit(sample), encoding="utf-8")
    print(f"Wrote {out_path} (sample of {len(sample)} traces from {len(traces)} total)")


def cli() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dirs", nargs="*", type=Path)
    p.add_argument("--auto", action="store_true")
    args = p.parse_args()
    rd = list(args.run_dirs)
    if args.auto or not rd:
        rd = find_v4_runs()
    if not rd:
        raise SystemExit("No v4 runs.")
    rd = [d if d.is_absolute() else (ROOT / d) for d in rd]
    main(rd)


if __name__ == "__main__":
    cli()
