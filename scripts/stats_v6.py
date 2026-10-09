"""V6 statistics — paired outcome-level comparisons for SAFE-Guard.

Reads ``results.rescored.json`` (written by ``rescore_tau2.py``) or, if
absent, ``results.json`` from one or more run directories and writes
``stats.md``, ``stats.csv`` and ``stats.json`` to the output directory
(default: the first run directory).

Design (chosen so that repeated seeds of one task are not treated as
independent observations):

- Rows with ``invalid`` or ``error`` set are excluded; the exclusions are
  counted per variant and reported.
- Each comparison pairs treatment and control by ``(task_id, seed)``. Pairs
  are then averaged per task, so the unit of inference is the task.
- Primary p-value: Wilcoxon signed-rank test on per-task mean differences
  (zeros dropped; p = 1 when every task difference is zero).
- Effect size: mean pair difference (treatment − control) with a 95%
  task-clustered bootstrap CI (``clustered_bootstrap_diff``).
- Binary metrics also report an exact McNemar test on the (task, seed)
  pairs as a sensitivity check; it ignores clustering and is not
  Holm-corrected.
- Holm correction is applied within each (family, tier) group: the primary
  family compares baseline, safe-prompt and safeguard; the ablation family
  compares safeguard with each single-rule-group ablation. Primary-tier
  metrics are the pre-registered outcome metrics; secondary metrics are
  exploratory.
- Per-domain ``primary-<domain>`` families repeat the primary comparisons
  within each domain; they are exploratory and corrected only within the
  domain family.
- Valid rows with no ``tau2_reward`` are counted per variant ("no reward").

Usage:
    python scripts/stats_v6.py outputs/runs/<run_dir> [<run_dir> ...]
        [--out DIR] [--n-boot N]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from scipy.stats import binomtest, wilcoxon

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_v4 import BOOT_N, RNG_SEED, clustered_bootstrap_diff, holm_correct  # noqa: E402

# Metric name -> (kind, tier). "success" is derived from tau2_reward.
METRICS: dict[str, tuple[str, str]] = {
    "any_unsafe_write": ("binary", "primary"),
    "commission_error": ("binary", "primary"),
    "success": ("binary", "primary"),
    "unsafe_extra_writes": ("count", "secondary"),
    "missed_gold_writes": ("count", "secondary"),
    "executed_writes": ("count", "secondary"),
    "transferred": ("binary", "secondary"),
    "unconfirmed_writes": ("count", "secondary"),
    "unauthenticated_writes": ("count", "secondary"),
    "blocked_calls": ("count", "secondary"),
}

# Lower is better for every metric except these.
HIGHER_IS_BETTER = {"success"}

PRIMARY_COMPARISONS = [
    ("safeguard-transaction", "baseline"),
    ("safeguard", "baseline"),
    ("safe-prompt", "baseline"),
    ("safeguard", "safe-prompt"),
]
ABLATIONS = ["safeguard-noS", "safeguard-noA", "safeguard-noF", "safeguard-noE"]
ABLATION_COMPARISONS = [("safeguard", a) for a in ABLATIONS]

VARIANT_ORDER = ["baseline", "safe-prompt", "safeguard", "safeguard-transaction", *ABLATIONS]


# --------------- Loading ---------------


def load_rows(run_dirs: list[Path]) -> list[dict]:
    """Load rows, preferring ``results.rescored.json`` (see rescore_tau2.py)."""
    rows: list[dict] = []
    for d in run_dirs:
        rj = d / "results.rescored.json"
        if not rj.exists():
            rj = d / "results.json"
        if not rj.exists():
            print(f"warning: {rj} not found", file=sys.stderr)
            continue
        print(f"loaded {rj}", file=sys.stderr)
        rows.extend(json.loads(rj.read_text(encoding="utf-8")))
    return rows


def is_valid(row: dict) -> bool:
    return not row.get("invalid") and not row.get("error")


def metric_value(row: dict, metric: str) -> float | None:
    if metric == "success":
        reward = row.get("tau2_reward")
        if reward is None:
            return None
        return 1.0 if float(reward) >= 1.0 - 1e-9 else 0.0
    value = row.get(metric)
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def index_rows(rows: list[dict]) -> dict[tuple[str, str, int], dict]:
    """Index valid rows by (variant, task_id, seed). Last write wins."""
    idx: dict[tuple[str, str, int], dict] = {}
    for r in rows:
        if not is_valid(r):
            continue
        idx[(r["agent_variant"], r["task_id"], int(r.get("seed", 0) or 0))] = r
    return idx


# --------------- Tests ---------------


def mcnemar_exact(pairs: list[tuple[float, float]]) -> tuple[int, int, float]:
    """Exact McNemar on binary pairs (treatment, control).

    Returns (b, c, p) where b = treatment 1 & control 0, c = treatment 0 &
    control 1.
    """
    b = sum(1 for x, y in pairs if x >= 0.5 and y < 0.5)
    c = sum(1 for x, y in pairs if x < 0.5 and y >= 0.5)
    if b + c == 0:
        return b, c, 1.0
    return b, c, float(binomtest(min(b, c), b + c, 0.5).pvalue)


def task_level_wilcoxon(task_diffs: list[float]) -> float:
    nonzero = [d for d in task_diffs if abs(d) > 1e-12]
    if not nonzero:
        return 1.0
    return float(wilcoxon(nonzero, zero_method="wilcox").pvalue)


def compare(
    idx: dict[tuple[str, str, int], dict],
    treatment: str,
    control: str,
    metric: str,
    n_boot: int = BOOT_N,
    seed: int = RNG_SEED,
) -> dict | None:
    kind, tier = METRICS[metric]
    triples: list[tuple[str, float, float]] = []
    for (variant, task_id, s), row in idx.items():
        if variant != treatment:
            continue
        other = idx.get((control, task_id, s))
        if other is None:
            continue
        x, y = metric_value(row, metric), metric_value(other, metric)
        if x is None or y is None:
            continue
        triples.append((task_id, x, y))
    if not triples:
        return None

    by_task: dict[str, list[float]] = defaultdict(list)
    for task_id, x, y in triples:
        by_task[task_id].append(x - y)
    task_diffs = [mean(v) for v in by_task.values()]

    obs, lo, hi, _ = clustered_bootstrap_diff(triples, n_boot=n_boot, seed=seed)
    result = {
        "treatment": treatment,
        "control": control,
        "metric": metric,
        "kind": kind,
        "tier": tier,
        "n_pairs": len(triples),
        "n_tasks": len(by_task),
        "treatment_mean": mean(x for _, x, _ in triples),
        "control_mean": mean(y for _, _, y in triples),
        "diff": obs,
        "ci_low": lo,
        "ci_high": hi,
        "tasks_better": sum(
            1 for d in task_diffs if (d > 1e-12 if metric in HIGHER_IS_BETTER else d < -1e-12)
        ),
        "tasks_worse": sum(
            1 for d in task_diffs if (d < -1e-12 if metric in HIGHER_IS_BETTER else d > 1e-12)
        ),
        "p_wilcoxon_task": task_level_wilcoxon(task_diffs),
        "mcnemar_b": None,
        "mcnemar_c": None,
        "p_mcnemar_pairs": None,
    }
    if kind == "binary":
        b, c, p = mcnemar_exact([(x, y) for _, x, y in triples])
        result.update(mcnemar_b=b, mcnemar_c=c, p_mcnemar_pairs=p)
    return result


def run_family(
    idx: dict[tuple[str, str, int], dict],
    family: str,
    comparisons: list[tuple[str, str]],
    n_boot: int,
) -> list[dict]:
    results: list[dict] = []
    for treatment, control in comparisons:
        for metric in METRICS:
            r = compare(idx, treatment, control, metric, n_boot=n_boot)
            if r is not None:
                r["family"] = family
                results.append(r)
    for tier in ("primary", "secondary"):
        group = [r for r in results if r["tier"] == tier]
        labels = [(f"{i}", r["p_wilcoxon_task"]) for i, r in enumerate(group)]
        for label, _, adj in holm_correct(labels):
            group[int(label)]["p_holm"] = adj
    return results


# --------------- Descriptives ---------------


def summarize(rows: list[dict], domain: str | None = None) -> list[dict]:
    by_variant: dict[str, list[dict]] = defaultdict(list)
    excluded: Counter[str] = Counter()
    for r in rows:
        if domain is not None and r.get("domain") != domain:
            continue
        if is_valid(r):
            by_variant[r["agent_variant"]].append(r)
        else:
            excluded[r["agent_variant"]] += 1

    out: list[dict] = []
    variants = [v for v in VARIANT_ORDER if v in by_variant or v in excluded]
    variants += sorted((set(by_variant) | set(excluded)) - set(variants))
    for v in variants:
        rs = by_variant.get(v, [])
        entry: dict = {
            "variant": v,
            "n_valid": len(rs),
            "n_excluded": excluded.get(v, 0),
            "n_missing_reward": sum(1 for r in rs if r.get("tau2_reward") is None),
        }
        for metric in METRICS:
            vals = [x for x in (metric_value(r, metric) for r in rs) if x is not None]
            entry[metric] = mean(vals) if vals else None
        rules: Counter[str] = Counter()
        for r in rs:
            rules.update(r.get("blocks_by_rule") or {})
        entry["blocks_by_rule"] = dict(sorted(rules.items()))
        out.append(entry)
    return out


# --------------- Output ---------------


def _fmt(x: float | None, digits: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{digits}f}"


def _fmt_p(p: float | None) -> str:
    if p is None:
        return "—"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def summary_table(summary: list[dict]) -> list[str]:
    cols = ["success", "any_unsafe_write", "commission_error", "unsafe_extra_writes",
            "missed_gold_writes", "transferred", "blocked_calls"]
    lines = [
        "| variant | n | excl. | no reward | " + " | ".join(cols) + " |",
        "|---|---|---|---|" + "---|" * len(cols),
    ]
    for e in summary:
        lines.append(
            f"| {e['variant']} | {e['n_valid']} | {e['n_excluded']} | "
            f"{e.get('n_missing_reward', 0)} | "
            + " | ".join(_fmt(e[c]) for c in cols)
            + " |"
        )
    return lines


def comparison_table(results: list[dict]) -> list[str]:
    lines = [
        "| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        mc = "—"
        if r["kind"] == "binary":
            mc = f"{r['mcnemar_b']}/{r['mcnemar_c']}, {_fmt_p(r['p_mcnemar_pairs'])}"
        lines.append(
            f"| {r['treatment']} vs {r['control']} | {r['metric']} | {r['tier']} | "
            f"{r['n_pairs']} | {r['n_tasks']} | {_fmt(r['treatment_mean'])} | "
            f"{_fmt(r['control_mean'])} | {_fmt(r['diff'])} [{_fmt(r['ci_low'])}, {_fmt(r['ci_high'])}] | "
            f"{r['tasks_better']}/{r['tasks_worse']} | {_fmt_p(r['p_wilcoxon_task'])} | "
            f"{_fmt_p(r.get('p_holm'))} | {mc} |"
        )
    return lines


def write_outputs(out_dir: Path, run_dirs: list[Path], rows: list[dict], results: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    overall = summarize(rows)
    domains = sorted({r.get("domain") for r in rows if r.get("domain")})
    per_domain = {d: summarize(rows, d) for d in domains}

    md: list[str] = ["# V6 statistics — SAFE-Guard outcome metrics", ""]
    md.append("Runs: " + ", ".join(f"`{d.name}`" for d in run_dirs))
    md.append("")
    md.append(
        "Unit of inference is the task: (task, seed) pairs are averaged per task before the "
        "Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% "
        "task-clustered bootstrap CI. Holm correction within each (family, tier). "
        "McNemar on pairs is a sensitivity check that ignores clustering. "
        "`unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and "
        "measure rule adherence, not independent safety."
    )
    md.append("")
    md.append("## Per-variant summary (all domains)")
    md.append("")
    md.extend(summary_table(overall))
    for d, s in per_domain.items():
        md.extend(["", f"## Per-variant summary — {d}", ""])
        md.extend(summary_table(s))
    md.extend(["", "## Blocks by rule", ""])
    for e in overall:
        if e["blocks_by_rule"]:
            rules = ", ".join(f"{k}: {v}" for k, v in e["blocks_by_rule"].items())
            md.append(f"- **{e['variant']}**: {rules}")
    families = ["primary", "ablation"]
    families += sorted({r["family"] for r in results} - set(families))
    for family in families:
        fam = [r for r in results if r["family"] == family]
        if not fam:
            continue
        if family.startswith("primary-"):
            title = f"Primary comparisons — {family.split('-', 1)[1]} only (exploratory)"
        else:
            title = f"{family.capitalize()} comparisons"
        md.extend(["", f"## {title}", ""])
        md.extend(comparison_table(fam))
    md.append("")
    (out_dir / "stats.md").write_text("\n".join(md), encoding="utf-8")

    fields = [
        "family", "treatment", "control", "metric", "kind", "tier", "n_pairs", "n_tasks",
        "treatment_mean", "control_mean", "diff", "ci_low", "ci_high", "tasks_better",
        "tasks_worse", "p_wilcoxon_task", "p_holm", "mcnemar_b", "mcnemar_c", "p_mcnemar_pairs",
    ]
    with (out_dir / "stats.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    (out_dir / "stats.json").write_text(
        json.dumps(
            {"runs": [str(d) for d in run_dirs], "summary": overall,
             "summary_by_domain": per_domain, "comparisons": results},
            indent=2,
        ),
        encoding="utf-8",
    )


def analyze(rows: list[dict], n_boot: int = BOOT_N) -> list[dict]:
    idx = index_rows(rows)
    present = {v for v, _, _ in idx}
    primary = [(t, c) for t, c in PRIMARY_COMPARISONS if t in present and c in present]
    ablation = [(t, c) for t, c in ABLATION_COMPARISONS if t in present and c in present]
    return run_family(idx, "primary", primary, n_boot) + run_family(idx, "ablation", ablation, n_boot)


def analyze_by_domain(rows: list[dict], n_boot: int = BOOT_N) -> list[dict]:
    """Primary comparisons restricted to each domain (family ``primary-<domain>``)."""
    results: list[dict] = []
    for domain in sorted({r.get("domain") for r in rows if r.get("domain")}):
        idx = index_rows([r for r in rows if r.get("domain") == domain])
        present = {v for v, _, _ in idx}
        comps = [(t, c) for t, c in PRIMARY_COMPARISONS if t in present and c in present]
        results += run_family(idx, f"primary-{domain}", comps, n_boot)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--n-boot", type=int, default=BOOT_N)
    args = parser.parse_args(argv)

    rows = load_rows(args.run_dirs)
    if not rows:
        print("no results found", file=sys.stderr)
        return 1
    results = analyze(rows, n_boot=args.n_boot) + analyze_by_domain(rows, n_boot=args.n_boot)
    out_dir = args.out or args.run_dirs[0]
    write_outputs(out_dir, args.run_dirs, rows, results)
    print(f"wrote {out_dir / 'stats.md'} ({len(results)} comparisons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
