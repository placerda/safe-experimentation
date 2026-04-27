"""V3 statistical analysis — McNemar on CVFR + TOST on tau2_reward + pass^k.

Reads results.json from one or more run directories and produces:
  - Paired McNemar tests (binary: cvfr_passed) per (domain, contrast),
    Holm-corrected within the H1/H3 contrast family.
  - TOST one-sided non-inferiority test on tau2_reward (Δ_NI = 0.05),
    paired bootstrap on the difference (safe_aware - baseline).
  - safe_pass^k reliability: per (variant, domain), proportion of tasks
    that pass CVFR in *all* k seeds.

Usage:
    python scripts/analyze_v3.py outputs/runs/<v2-run> outputs/runs/<sweep-run-1> ...
    python scripts/analyze_v3.py --auto   # picks v2 + most recent v3 sweep dirs

Output:
    outputs/reports/v3_stats.md
    outputs/reports/v3_stats.json
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent

# ---------------------- Stat helpers (no scipy required) -----------------

def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact mid-p McNemar test on discordant pairs (b, c).

    Uses the binomial(b+c, 0.5) reference distribution. Returns 1.0 if
    b+c == 0 (no discordant pairs => no evidence of difference).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # P(X <= k) under Bin(n, 0.5)
    cum = 0.0
    for i in range(k + 1):
        cum += math.comb(n, i)
    p_one_sided = cum / (2 ** n)
    return min(1.0, 2 * p_one_sided)


def holm_correct(pvals: list[tuple[str, float]]) -> list[tuple[str, float, float]]:
    """Holm-Bonferroni: returns list of (label, raw_p, adj_p) sorted by raw_p."""
    m = len(pvals)
    sorted_p = sorted(pvals, key=lambda x: x[1])
    adj: list[tuple[str, float, float]] = []
    running_max = 0.0
    for i, (label, p) in enumerate(sorted_p):
        a = min(1.0, (m - i) * p)
        running_max = max(running_max, a)
        adj.append((label, p, running_max))
    return adj


def bootstrap_ci(diffs: list[float], n_boot: int = 5000, alpha: float = 0.05,
                 seed: int = 1234) -> tuple[float, float, float]:
    """Percentile bootstrap (mean) CI. Returns (mean, lo, hi)."""
    import random
    if not diffs:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(n_boot):
        means.append(mean(rng.choice(diffs) for _ in range(n)))
    means.sort()
    lo = means[int(n_boot * alpha / 2)]
    hi = means[int(n_boot * (1 - alpha / 2))]
    return (mean(diffs), lo, hi)


# ---------------------- Data loading --------------------------------------

def load_runs(run_dirs: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for d in run_dirs:
        p = d / "results.json"
        if not p.exists():
            print(f"!! skipping {d}: no results.json")
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            r["_run"] = d.name
            rows.append(r)
    return rows


def index_by_taskvariantseed(rows: list[dict]) -> dict:
    """Build {(domain, task_id, variant, seed): row}, deduplicating by latest run."""
    idx: dict = {}
    for r in rows:
        if r.get("error"):
            continue
        key = (r["domain"], r["task_id"], r["agent_variant"], int(r.get("seed", 0)))
        # Last write wins (deterministic if input is sorted by run name).
        idx[key] = r
    return idx


# ---------------------- Analyses ------------------------------------------

def analyse_cvfr_mcnemar(idx: dict, contrasts: list[tuple[str, str]]) -> list[dict]:
    """For each (domain, contrast=A-vs-B), build paired CVFR table over the
    intersection of (task_id, seed) where both A and B have a non-error result.
    """
    out: list[dict] = []
    domains = sorted({k[0] for k in idx})
    raw_p_for_holm: list[tuple[str, float]] = []
    rows_to_emit: list[dict] = []
    for domain in domains:
        for a, b in contrasts:
            pairs = []
            for (d, t, v, s), r in idx.items():
                if d != domain or v != a:
                    continue
                other = idx.get((d, t, b, s))
                if other is None:
                    continue
                pairs.append((bool(r.get("cvfr_passed")), bool(other.get("cvfr_passed"))))
            if not pairs:
                continue
            n = len(pairs)
            both = sum(1 for x, y in pairs if x and y)
            only_a = sum(1 for x, y in pairs if x and not y)
            only_b = sum(1 for x, y in pairs if not x and y)
            neither = sum(1 for x, y in pairs if not x and not y)
            p_a = (both + only_a) / n
            p_b = (both + only_b) / n
            p = mcnemar_exact_p(only_a, only_b)
            label = f"{domain}: {a} vs {b}"
            raw_p_for_holm.append((label, p))
            rows_to_emit.append({
                "domain": domain, "contrast": f"{a}_vs_{b}",
                "n_pairs": n,
                f"cvfr_{a}": round(p_a, 4),
                f"cvfr_{b}": round(p_b, 4),
                "delta": round(p_a - p_b, 4),
                "discordant_a_only": only_a,
                "discordant_b_only": only_b,
                "p_raw": round(p, 5),
            })
    holm = {label: adj for label, _, adj in holm_correct(raw_p_for_holm)}
    for r in rows_to_emit:
        label = f"{r['domain']}: {r['contrast'].replace('_vs_', ' vs ')}"
        r["p_holm"] = round(holm.get(label, r["p_raw"]), 5)
        out.append(r)
    return out


def analyse_tost_reward(idx: dict, delta_ni: float = 0.05) -> list[dict]:
    """Paired bootstrap CI of tau2_reward(safe-aware) - tau2_reward(baseline)
    per domain. NI met iff lower 95% CI > -delta_ni.
    """
    out: list[dict] = []
    domains = sorted({k[0] for k in idx})
    for domain in domains:
        diffs = []
        for (d, t, v, s), r in idx.items():
            if d != domain or v != "safe-aware":
                continue
            base = idx.get((d, t, "baseline", s))
            if base is None:
                continue
            diffs.append(float(r.get("tau2_reward") or 0) - float(base.get("tau2_reward") or 0))
        if not diffs:
            continue
        m, lo, hi = bootstrap_ci(diffs)
        out.append({
            "domain": domain,
            "n_pairs": len(diffs),
            "mean_diff": round(m, 4),
            "ci95_lo": round(lo, 4),
            "ci95_hi": round(hi, 4),
            "delta_ni": delta_ni,
            "non_inferior": lo > -delta_ni,
        })
    return out


def analyse_pass_at_k(idx: dict) -> list[dict]:
    """For each (domain, variant), compute pass^k = fraction of tasks where
    CVFR=1 across ALL seeds present (k = min seeds-per-task in that cell).
    """
    by_cell = defaultdict(lambda: defaultdict(list))  # (domain,variant) -> task_id -> [bool]
    for (d, t, v, s), r in idx.items():
        by_cell[(d, v)][t].append(bool(r.get("cvfr_passed")))
    out: list[dict] = []
    for (d, v), tasks in sorted(by_cell.items()):
        seed_counts = [len(seeds) for seeds in tasks.values()]
        if not seed_counts:
            continue
        k_min = min(seed_counts)
        pass_all = sum(1 for seeds in tasks.values() if all(seeds))
        out.append({
            "domain": d, "variant": v,
            "n_tasks": len(tasks),
            "seeds_per_task_min": k_min,
            "seeds_per_task_max": max(seed_counts),
            f"pass_at_{k_min}": round(pass_all / len(tasks), 4),
        })
    return out


# ---------------------- Reporting -----------------------------------------

def render_md(mc: list[dict], tost: list[dict], pak: list[dict]) -> str:
    lines = ["# V3 Statistical Analysis (auto-generated)", ""]
    lines.append("## H1/H3: Paired McNemar on CVFR")
    lines.append("Holm-corrected within the contrast family.\n")
    if mc:
        keys = list(mc[0].keys())
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("| " + " | ".join("---" for _ in keys) + " |")
        for r in mc:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    else:
        lines.append("_no contrasts had paired data_")
    lines.extend(["", "## H2: TOST non-inferiority on tau2_reward (Δ_NI = 0.05)",
                  "_safe-aware vs baseline; non_inferior iff CI95 lower bound > -0.05_\n"])
    if tost:
        keys = list(tost[0].keys())
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("| " + " | ".join("---" for _ in keys) + " |")
        for r in tost:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    else:
        lines.append("_no paired data_")
    lines.extend(["", "## Reliability: safe_pass^k", ""])
    if pak:
        keys = list(pak[0].keys())
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("| " + " | ".join("---" for _ in keys) + " |")
        for r in pak:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    return "\n".join(lines) + "\n"


# ---------------------- Main ---------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="*", type=Path)
    ap.add_argument("--auto", action="store_true", help="auto-pick v2 gpt-4.1 + recent v3 dirs")
    ap.add_argument("--out-md", type=Path, default=ROOT / "outputs" / "reports" / "v3_stats.md")
    ap.add_argument("--out-json", type=Path, default=ROOT / "outputs" / "reports" / "v3_stats.json")
    args = ap.parse_args()

    run_dirs = list(args.run_dirs)
    if args.auto:
        runs_root = ROOT / "outputs" / "runs"
        for d in sorted(runs_root.iterdir()):
            if d.is_dir() and ("__gpt-4.1" in d.name or "__v3-" in d.name):
                run_dirs.append(d)
    if not run_dirs:
        raise SystemExit("no run directories provided (use --auto or pass paths)")

    rows = load_runs(run_dirs)
    idx = index_by_taskvariantseed(rows)
    print(f"Loaded {len(rows)} rows, {len(idx)} unique (domain,task,variant,seed) cells")

    contrasts = [
        ("safe-aware", "baseline"),
        ("safe-aware", "prompt-only"),
        ("safe-aware", "binding-only"),
        ("binding-only", "baseline"),
        ("prompt-only", "baseline"),
    ]
    mc = analyse_cvfr_mcnemar(idx, contrasts)
    tost = analyse_tost_reward(idx)
    pak = analyse_pass_at_k(idx)

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_md(mc, tost, pak), encoding="utf-8")
    args.out_json.write_text(json.dumps({
        "mcnemar_cvfr": mc, "tost_reward": tost, "pass_at_k": pak,
        "input_runs": [d.name for d in run_dirs],
    }, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
