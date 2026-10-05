"""V4 statistical analysis — per-dimension paired bootstrap + Holm.

Reads results.json from one or more run directories and produces:

  - Per-dimension means by (domain, variant) (S, A, F, E, CVFR, reward).
  - SAFE-aware vs baseline differences per metric: task-clustered bootstrap
    resampling tasks with replacement. Reports 95% CIs and two-sided bootstrap
    p-values, with Holm correction across metrics.
  - H1' family (4 contrasts): for each dimension D and its target
    variant X(D), task-clustered bootstrap on Δ = mean(X(D)) − mean(baseline)
    on the continuous score for D. Two-sided 95% CI + p-value.
    Holm-corrected within the family of 4.
  - H3' descriptive: per dimension, gap between all-guardrails and the
    best single-enforcer variant for that dimension. 95% CI of the gap.
  - Guardrail event firing rates per (variant, enforcer, action).

Usage:
    python scripts/analyze_v4.py outputs/runs/<run1> outputs/runs/<run2> ...
    python scripts/analyze_v4.py --auto   # picks most recent v4 dirs

Output:
    outputs/reports/v4_stats.md
    outputs/reports/v4_stats.json
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent

DIMENSIONS = [
    ("scope", "S", "binding"),
    ("anchored_decisions", "A", "evidence"),
    ("flow_integrity", "F", "flow"),
    ("escalation", "E", "escalation"),
]
GUARDRAIL_VARIANTS = ["binding", "evidence", "flow", "escalation", "all-guardrails"]
BOOT_N = 10_000
RNG_SEED = 20260429


# --------------- Stat helpers (no scipy) ---------------


def clustered_bootstrap_diff(
    paired_values: list[tuple[str, float, float]],
    n_boot: int = BOOT_N,
    seed: int = RNG_SEED,
) -> tuple[float, float, float, float]:
    """Task-clustered bootstrap on paired differences.

    ``paired_values`` contains (task_id, x, y). Resampling draws task IDs with
    replacement and includes all paired observations for each selected task.
    Returns (observed_diff, ci_low_95, ci_high_95, two_sided_p), where the
    p-value is centered on the null by comparing bootstrap deviations from the
    observed estimate against zero.
    """
    if not paired_values:
        return 0.0, 0.0, 0.0, 1.0

    by_task: dict[str, list[float]] = defaultdict(list)
    for task_id, x, y in paired_values:
        by_task[task_id].append(x - y)

    task_ids = sorted(by_task)
    diffs = [d for values in by_task.values() for d in values]
    obs = mean(diffs)
    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_boot):
        sample_diffs: list[float] = []
        for _ in task_ids:
            sample_diffs.extend(by_task[rng.choice(task_ids)])
        boot_means.append(sum(sample_diffs) / len(sample_diffs))

    boot_means.sort()
    lo = boot_means[int(0.025 * n_boot)]
    hi = boot_means[int(0.975 * n_boot) - 1]
    centered = [b - obs for b in boot_means]
    p_left = sum(1 for b in centered if b <= -abs(obs)) / n_boot
    p_right = sum(1 for b in centered if b >= abs(obs)) / n_boot
    return obs, lo, hi, min(1.0, 2 * min(p_left, p_right))


def holm_correct(pvals: list[tuple[str, float]]) -> list[tuple[str, float, float]]:
    m = len(pvals)
    sorted_p = sorted(pvals, key=lambda x: x[1])
    adj: list[tuple[str, float, float]] = []
    running_max = 0.0
    for i, (label, p) in enumerate(sorted_p):
        a = min(1.0, (m - i) * p)
        running_max = max(running_max, a)
        adj.append((label, p, running_max))
    return adj


# --------------- Data loading ---------------


def load_runs(run_dirs: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for d in run_dirs:
        rj = d / "results.json"
        if not rj.exists():
            continue
        rows.extend(json.loads(rj.read_text(encoding="utf-8")))
    return rows


def index_by_cell(rows: list[dict]) -> dict[tuple[str, str, str, int], dict]:
    """Index by (variant, domain, task_id, seed). Last-write-wins on duplicates."""
    idx: dict[tuple[str, str, str, int], dict] = {}
    for r in rows:
        key = (r["agent_variant"], r["domain"], r["task_id"], r.get("seed", 0))
        idx[key] = r
    return idx


def paired_arrays(
    idx: dict, variant_a: str, variant_b: str, domain: str, dim_key: str
) -> tuple[list[float], list[float], list[tuple[str, int]]]:
    """Return aligned arrays restricted to cells present in both variants."""
    pairs = paired_values(idx, variant_a, variant_b, domain, dim_key)
    return [x for _, x, _ in pairs], [y for _, _, y in pairs], [(tid, 0) for tid, _, _ in pairs]


def paired_values(
    idx: dict, variant_a: str, variant_b: str, domain: str, dim_key: str
) -> list[tuple[str, float, float]]:
    """Return aligned (task_id, x_a, x_b) for cells present in both variants."""
    keys_a = {k for k in idx if k[0] == variant_a and k[1] == domain}
    keys_b = {k for k in idx if k[0] == variant_b and k[1] == domain}
    paired_keys = sorted({(k[2], k[3]) for k in keys_a} & {(k[2], k[3]) for k in keys_b})
    pairs: list[tuple[str, float, float]] = []
    for tid, seed in paired_keys:
        ra = idx.get((variant_a, domain, tid, seed))
        rb = idx.get((variant_b, domain, tid, seed))
        if ra is None or rb is None:
            continue
        va = ra.get(dim_key)
        vb = rb.get(dim_key)
        if va is None or vb is None:
            continue
        pairs.append((tid, float(va), float(vb)))
    return pairs




# --------------- Main analysis ---------------


def main(run_dirs: list[Path]) -> None:
    rows = load_runs(run_dirs)
    if not rows:
        raise SystemExit("No results.json rows found in supplied run dirs.")
    idx = index_by_cell(rows)

    variants = sorted({r["agent_variant"] for r in rows})
    domains = sorted({r["domain"] for r in rows})

    out: dict = {
        "n_rows": len(rows),
        "n_unique_cells": len(idx),
        "variants": variants,
        "domains": domains,
        "run_dirs": [str(d) for d in run_dirs],
    }

    # ---- Per-(variant, domain) means
    means: dict[str, dict[str, dict[str, float]]] = {}
    for v in variants:
        means[v] = {}
        for d in domains:
            cells = [idx[k] for k in idx if k[0] == v and k[1] == d]
            if not cells:
                continue
            n = len(cells)
            means[v][d] = {
                "n": n,
                "scope": mean(c.get("scope", 0) for c in cells),
                "anchored_decisions": mean(c.get("anchored_decisions", 0) for c in cells),
                "flow_integrity": mean(c.get("flow_integrity", 0) for c in cells),
                "escalation": mean(c.get("escalation", 0) for c in cells),
                "cvfr_pass_rate": sum(1 for c in cells if c.get("cvfr_passed")) / n,
                "tau2_reward": mean(c.get("tau2_reward") or 0.0 for c in cells if c.get("tau2_reward") is not None) if any(c.get("tau2_reward") is not None for c in cells) else None,
            }
    out["means"] = means

    # ---- H1' family — per-dimension lift, paired bootstrap, Holm within 4
    h1_results: list[dict] = []
    h1_pvals: list[tuple[str, float]] = []
    for dim_key, dim_label, target in DIMENSIONS:
        for d in domains:
            pairs = paired_values(idx, target, "baseline", d, dim_key)
            if not pairs:
                continue
            obs, lo, hi, p = clustered_bootstrap_diff(pairs)
            label = f"H1_{dim_label}_{d}"
            h1_results.append({
                "label": label, "dimension": dim_label, "domain": d,
                "target_variant": target, "n_pairs": len(pairs),
                "delta_mean": obs, "ci95_low": lo, "ci95_high": hi, "p_value": p,
            })
            h1_pvals.append((label, p))

    holm = holm_correct(h1_pvals)
    holm_map = {lbl: (raw, adj) for lbl, raw, adj in holm}
    for r in h1_results:
        raw, adj = holm_map[r["label"]]
        r["p_holm"] = adj
        r["reject_h0"] = adj < 0.05
    out["h1_per_dimension"] = h1_results

    # ---- SAFE-aware vs baseline differences per metric, Holm across metrics
    metric_results: list[dict] = []
    metric_pvals: list[tuple[str, float]] = []
    metrics = ["scope", "anchored_decisions", "flow_integrity", "escalation", "safe_overall", "tau2_reward"]
    if "safe-aware" in variants:
        for metric in metrics:
            for d in domains:
                pairs = paired_values(idx, "safe-aware", "baseline", d, metric)
                if not pairs:
                    continue
                obs, lo, hi, p = clustered_bootstrap_diff(pairs)
                label = f"safe_aware_vs_baseline_{metric}_{d}"
                metric_results.append({
                    "label": label, "metric": metric, "domain": d,
                    "n_pairs": len(pairs), "n_tasks": len({tid for tid, _, _ in pairs}),
                    "delta_mean": obs, "ci95_low": lo, "ci95_high": hi, "p_value": p,
                })
                metric_pvals.append((label, p))
    holm = holm_correct(metric_pvals)
    holm_map = {lbl: (raw, adj) for lbl, raw, adj in holm}
    for r in metric_results:
        _raw, adj = holm_map[r["label"]]
        r["p_holm"] = adj
        r["reject_h0"] = adj < 0.05
    out["safe_aware_vs_baseline"] = metric_results

    # ---- H3' descriptive — composability of all-guardrails
    h3_results: list[dict] = []
    if "all-guardrails" in variants:
        for dim_key, dim_label, target in DIMENSIONS:
            for d in domains:
                pairs = paired_values(idx, "all-guardrails", target, d, dim_key)
                if not pairs:
                    continue
                obs, lo, hi, _ = clustered_bootstrap_diff(pairs)
                h3_results.append({
                    "dimension": dim_label, "domain": d,
                    "n_pairs": len(pairs),
                    "delta_mean_vs_target": obs,
                    "ci95_low": lo, "ci95_high": hi,
                    "interpretation": (
                        "all-guardrails matches or beats target"
                        if lo >= -0.02 else "all-guardrails worse than target"
                    ),
                })
    out["h3_composability"] = h3_results

    # ---- Guardrail event firing rates
    event_summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for d in run_dirs:
        traces_dir = d / "traces"
        if not traces_dir.exists():
            continue
        for fp in traces_dir.glob("*.json"):
            try:
                tr = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            v = tr.get("agent_variant", "?")
            for e in tr.get("metadata", {}).get("guardrail_events", []):
                key = f"{e.get('enforcer','?')}/{e.get('action','?')}"
                event_summary[v][key] += 1
    out["guardrail_events"] = {v: dict(d) for v, d in event_summary.items()}

    # ---- Persist outputs
    out_dir = ROOT / "outputs" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "v4_stats.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Markdown summary
    lines: list[str] = []
    lines.append("# v4 statistical analysis\n")
    lines.append(f"- Source runs: {[str(d.name) for d in run_dirs]}")
    lines.append(f"- Total rows: {out['n_rows']}, unique cells: {out['n_unique_cells']}")
    lines.append(f"- Variants: {variants}")
    lines.append(f"- Domains: {domains}\n")

    lines.append("## Per-(variant, domain) means\n")
    lines.append("| variant | domain | n | S | A | F | E | CVFR | reward |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for v in variants:
        for d in domains:
            m = means.get(v, {}).get(d)
            if not m:
                continue
            r = "—" if m["tau2_reward"] is None else f"{m['tau2_reward']:.3f}"
            lines.append(
                f"| {v} | {d} | {m['n']} | {m['scope']:.3f} | {m['anchored_decisions']:.3f} "
                f"| {m['flow_integrity']:.3f} | {m['escalation']:.3f} | {m['cvfr_pass_rate']:.3f} | {r} |"
            )
    lines.append("")

    lines.append("## H1' — per-dimension lift (paired bootstrap, Holm within 4)\n")
    lines.append("| dimension | domain | target | n | Δ mean | 95% CI | p | p_holm | reject H0 |")
    lines.append("|---|---|---|---:|---:|---|---:|---:|---|")
    for r in h1_results:
        lines.append(
            f"| {r['dimension']} | {r['domain']} | {r['target_variant']} | {r['n_pairs']} "
            f"| {r['delta_mean']:+.3f} | [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}] "
            f"| {r['p_value']:.3f} | {r['p_holm']:.3f} | {'**yes**' if r['reject_h0'] else 'no'} |"
        )
    lines.append("")

    lines.append("## SAFE-aware vs baseline (task-clustered bootstrap, Holm across metrics)\n")
    lines.append("| metric | domain | pairs | tasks | Δ mean | 95% CI | p | p_holm | reject H0 |")
    lines.append("|---|---|---:|---:|---:|---|---:|---:|---|")
    for r in metric_results:
        lines.append(
            f"| {r['metric']} | {r['domain']} | {r['n_pairs']} | {r['n_tasks']} "
            f"| {r['delta_mean']:+.3f} | [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}] "
            f"| {r['p_value']:.3f} | {r['p_holm']:.3f} | {'**yes**' if r['reject_h0'] else 'no'} |"
        )
    lines.append("")

    lines.append("## H3' — composability (all-guardrails vs single-enforcer target)\n")
    lines.append("| dimension | domain | n | Δ vs target | 95% CI | interpretation |")
    lines.append("|---|---|---:|---:|---|---|")
    for r in h3_results:
        lines.append(
            f"| {r['dimension']} | {r['domain']} | {r['n_pairs']} "
            f"| {r['delta_mean_vs_target']:+.3f} | [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}] "
            f"| {r['interpretation']} |"
        )
    lines.append("")

    lines.append("## Guardrail event firing summary\n")
    for v, d in out["guardrail_events"].items():
        lines.append(f"- **{v}**: {d}")
    lines.append("")

    (out_dir / "v4_stats.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_dir / 'v4_stats.md'} and {out_dir / 'v4_stats.json'}")


# --------------- CLI ---------------


def find_v4_runs() -> list[Path]:
    runs_dir = ROOT / "outputs" / "runs"
    if not runs_dir.exists():
        return []
    candidates = [
        d for d in runs_dir.iterdir()
        if d.is_dir() and ("v4" in d.name.lower())
        and not d.name.endswith("smoke-v4-bind")
        and "smoke" not in d.name
    ]
    return sorted(candidates)


def cli() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dirs", nargs="*", type=Path)
    p.add_argument("--auto", action="store_true", help="Pick non-smoke v4 run dirs automatically.")
    args = p.parse_args()
    run_dirs = list(args.run_dirs)
    if args.auto or not run_dirs:
        run_dirs = find_v4_runs()
    if not run_dirs:
        raise SystemExit("No v4 run dirs found.")
    run_dirs = [d if d.is_absolute() else (ROOT / d) for d in run_dirs]
    print(f"Analyzing: {[d.name for d in run_dirs]}")
    main(run_dirs)


if __name__ == "__main__":
    cli()
