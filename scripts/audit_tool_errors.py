"""Audit tool-call error rates across experiment runs.

Detects the harness bug where the runner unpacked ``_load_domain_env`` in the
wrong order, so every tool call was dispatched to the toolkit instead of the
environment and failed with ``object has no attribute 'get_response'``.

Usage:
    python scripts/audit_tool_errors.py --runs-dir outputs/runs [--runs-dir ...]
        [--out outputs/audit/tool_error_audit.md]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HARNESS_SIGNATURE = "has no attribute 'get_response'"


def classify(result: object) -> str:
    text = "" if result is None else str(result)
    if HARNESS_SIGNATURE in text:
        return "harness_bug"
    if text.startswith("Error") or text.startswith("[BLOCKED") or "BLOCKED" in text[:40]:
        return "error_or_block"
    return "ok"


def audit_run(run_dir: Path) -> dict:
    traces_dir = run_dir / "traces"
    totals: Counter = Counter()
    by_variant: dict[str, Counter] = defaultdict(Counter)
    n_traces = 0
    for path in sorted(traces_dir.glob("*.json")):
        try:
            trace = json.loads(path.read_bytes().decode("utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            totals["unreadable_trace"] += 1
            continue
        n_traces += 1
        variant = trace.get("agent_variant", "?")
        for call in trace.get("tool_calls_log") or []:
            if call.get("blocked"):
                kind = "blocked"
            else:
                kind = classify(call.get("result"))
            totals[kind] += 1
            totals["calls"] += 1
            by_variant[variant][kind] += 1
            by_variant[variant]["calls"] += 1
    return {"run": run_dir.name, "traces": n_traces, "totals": totals, "by_variant": by_variant}


def rate(c: Counter, key: str) -> float:
    return c[key] / c["calls"] if c["calls"] else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", action="append", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("outputs/audit/tool_error_audit.md"))
    args = ap.parse_args()

    results = []
    for runs_dir in args.runs_dir:
        for run_dir in sorted(p for p in runs_dir.iterdir() if (p / "traces").is_dir()):
            results.append((runs_dir, audit_run(run_dir)))

    lines = [
        "# Tool-call error audit",
        "",
        f"Harness-bug signature: `{HARNESS_SIGNATURE}`.",
        "A run is **INVALID** when more than 5% of its tool calls hit the harness bug.",
        "",
        "| Source | Run | Traces | Tool calls | Harness-bug rate | Other error/block rate | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    payload = []
    for runs_dir, r in results:
        t = r["totals"]
        hb = rate(t, "harness_bug")
        other = (t["error_or_block"] + t["blocked"]) / t["calls"] if t["calls"] else 0.0
        status = "INVALID" if hb > 0.05 else ("no tool calls" if not t["calls"] else "ok")
        lines.append(
            f"| `{runs_dir}` | `{r['run']}` | {r['traces']} | {t['calls']} | {hb:.1%} | {other:.1%} | {status} |"
        )
        payload.append(
            {
                "source": str(runs_dir),
                "run": r["run"],
                "traces": r["traces"],
                "calls": t["calls"],
                "harness_bug_rate": hb,
                "other_error_or_block_rate": other,
                "status": status,
                "by_variant": {v: dict(c) for v, c in r["by_variant"].items()},
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
