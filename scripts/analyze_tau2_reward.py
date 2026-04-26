"""Extra stats: τ³-bench reward paired analysis.

Complements scripts/analyze_results.py by reporting the official
τ³-bench reward (where computable) for each variant, including a
paired sign-test comparing baseline vs safe-aware on the subset of
tasks where both runs produced a non-None reward.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats


def load(run_dir: Path) -> list[dict]:
    return json.loads((run_dir / "results.json").read_text(encoding="utf-8"))


def stats_for(rewards: list[float]) -> dict:
    if not rewards:
        return {"n": 0, "mean": None, "ci_lo": None, "ci_hi": None}
    arr = np.asarray(rewards, dtype=float)
    rng = np.random.default_rng(seed=42)
    boots = rng.choice(arr, size=(10000, len(arr)), replace=True).mean(axis=1)
    return {
        "n": len(arr),
        "mean": float(arr.mean()),
        "ci_lo": float(np.quantile(boots, 0.025)),
        "ci_hi": float(np.quantile(boots, 0.975)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    data = load(run_dir)

    by_v = defaultdict(list)
    by_v_dom = defaultdict(list)
    by_pair = defaultdict(dict)
    for r in data:
        by_v[r["agent_variant"]].append(r)
        by_v_dom[(r["agent_variant"], r["domain"])].append(r)
        by_pair[r["task_id"]][r["agent_variant"]] = r

    lines: list[str] = ["# τ³-bench Official Reward Analysis", ""]
    lines.append(f"Run: `{run_dir}`")
    lines.append("")
    lines.append("τ³-bench reward = action-matching × DB-state-match × communicate-info × NL-assertions")
    lines.append("(only the components in each task's `reward_basis` are multiplied; final reward in [0,1])")
    lines.append("")

    # Per-variant means with bootstrap CI
    lines.append("## Per-variant reward (subset where evaluator succeeded)")
    lines.append("")
    lines.append("| variant | domain | n | mean | 95% bootstrap CI |")
    lines.append("|---|---|---:|---:|---|")
    for v in ["baseline", "safe-aware"]:
        rewards = [r["tau2_reward"] for r in by_v[v] if r["tau2_reward"] is not None]
        s = stats_for(rewards)
        ci = (
            f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]"
            if s["mean"] is not None
            else "n/a"
        )
        mean_str = f"{s['mean']:.3f}" if s["mean"] is not None else "n/a"
        lines.append(f"| {v} | all | {s['n']} | {mean_str} | {ci} |")
        for d in ["airline", "retail"]:
            rewards = [
                r["tau2_reward"]
                for r in by_v_dom[(v, d)]
                if r["tau2_reward"] is not None
            ]
            s = stats_for(rewards)
            ci = (
                f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]"
                if s["mean"] is not None
                else "n/a"
            )
            mean_str = f"{s['mean']:.3f}" if s["mean"] is not None else "n/a"
            lines.append(f"| {v} | {d} | {s['n']} | {mean_str} | {ci} |")
    lines.append("")

    # Paired test
    paired = []
    for tid, vs in by_pair.items():
        if "baseline" in vs and "safe-aware" in vs:
            b = vs["baseline"]["tau2_reward"]
            s = vs["safe-aware"]["tau2_reward"]
            if b is not None and s is not None:
                paired.append((tid, b, s))

    lines.append("## Paired comparison (both variants successfully evaluated)")
    lines.append("")
    lines.append(f"Paired tasks: **{len(paired)}**")
    lines.append("")
    if paired:
        diffs = np.array([s - b for _, b, s in paired], dtype=float)
        mean_diff = float(diffs.mean())
        n_pos = int((diffs > 0).sum())
        n_neg = int((diffs < 0).sum())
        n_tie = int((diffs == 0).sum())
        # Sign test on non-zero diffs
        nonzero = int(n_pos + n_neg)
        if nonzero > 0:
            p_sign = float(stats.binomtest(n_pos, nonzero, 0.5).pvalue)
        else:
            p_sign = None
        # Wilcoxon (will fall back if too many ties)
        try:
            res = stats.wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
            p_wilcox = float(res.pvalue)
        except Exception:
            p_wilcox = None

        lines.append(f"- Mean Δ (safe-aware − baseline): **{mean_diff:+.3f}**")
        lines.append(f"- safe-aware better on {n_pos} tasks; baseline better on {n_neg}; tie on {n_tie}")
        if p_sign is not None:
            lines.append(f"- Sign test (excluding ties): p = {p_sign:.4f}")
        if p_wilcox is not None:
            lines.append(f"- Wilcoxon signed-rank: p = {p_wilcox:.4f}")
    lines.append("")

    # Coverage
    lines.append("## Evaluator coverage")
    lines.append("")
    for v in ["baseline", "safe-aware"]:
        n = len(by_v[v])
        n_eval = sum(1 for r in by_v[v] if r["tau2_reward"] is not None)
        lines.append(f"- {v}: {n_eval}/{n} traces had a valid τ³-bench reward")
    lines.append("")
    lines.append("Notes on missing rewards (`t3:n/a`):")
    lines.append("- Tasks whose `reward_basis` includes `NL_ASSERTION` require an LLM judge call;")
    lines.append("  this run did not configure that judge so those evaluations fail safely.")
    lines.append("- Some retail traces with rejected actions raise replay errors when tau2 re-executes")
    lines.append("  mutating tools — these are flagged in the `tau2_note` field of `results.json`.")
    lines.append("")

    out_path = Path("outputs/reports/tau2_reward_analysis.md")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    print()
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
