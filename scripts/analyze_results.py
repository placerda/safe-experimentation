"""Analyze experiment results — comparison tables, divergence cases, paper examples.

Usage:
    python scripts/analyze_results.py [--run-dir outputs/runs/<run-id>]
    python scripts/analyze_results.py --latest
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats


def load_results(results_path: Path) -> list[dict[str, Any]]:
    with open(results_path) as f:
        return json.load(f)


def find_latest_run(output_dir: Path) -> Path | None:
    runs_dir = output_dir / "runs"
    if not runs_dir.exists():
        return None
    runs = sorted(runs_dir.iterdir(), reverse=True)
    return runs[0] if runs else None


def print_comparison_table(results: list[dict]) -> None:
    """Print aggregate comparison between agent variants."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in results:
        key = (r["domain"], r["agent_variant"])
        groups[key].append(r)

    print("\n=== Aggregate Comparison ===")
    print(f"{'domain':<10} {'variant':<12} {'n':>3} {'scope':>6} {'anchor':>7} {'flow':>6} {'escal':>6} {'SAFE':>6}")
    print("-" * 65)

    for (domain, variant), items in sorted(groups.items()):
        n = len(items)
        avg = lambda k: sum(r[k] for r in items) / n
        print(
            f"{domain:<10} {variant:<12} {n:>3} "
            f"{avg('scope'):>6.2f} {avg('anchored_decisions'):>7.2f} "
            f"{avg('flow_integrity'):>6.2f} {avg('escalation'):>6.2f} "
            f"{avg('safe_overall'):>6.2f}"
        )


def print_per_task_table(results: list[dict]) -> None:
    """Print per-task scores for all variants side by side."""
    # Group by task_id
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_task[r["task_id"]][r["agent_variant"]] = r

    print("\n=== Per-Task Comparison ===")
    print(f"{'task_id':<15} {'variant':<12} {'scope':>6} {'anchor':>7} {'flow':>6} {'escal':>6} {'SAFE':>6}")
    print("-" * 65)

    for task_id in sorted(by_task.keys()):
        for variant in sorted(by_task[task_id].keys()):
            r = by_task[task_id][variant]
            print(
                f"{task_id:<15} {variant:<12} "
                f"{r['scope']:>6.2f} {r['anchored_decisions']:>7.2f} "
                f"{r['flow_integrity']:>6.2f} {r['escalation']:>6.2f} "
                f"{r['safe_overall']:>6.2f}"
            )


def find_divergence_cases(results: list[dict]) -> list[dict]:
    """Find cases where task success and SAFE compliance diverge."""
    divergences = []
    for r in results:
        if r.get("task_completed") and r["safe_overall"] < 0.5:
            divergences.append({
                **r,
                "divergence_type": "task_success_but_safe_failure",
                "note": "Task completed but SAFE score below 0.5",
            })
        elif not r.get("task_completed") and r["safe_overall"] >= 0.75:
            divergences.append({
                **r,
                "divergence_type": "safe_compliance_but_task_incomplete",
                "note": "SAFE score high but task not completed",
            })
    return divergences


def find_variant_differences(results: list[dict]) -> list[dict]:
    """Find tasks where baseline and SAFE-aware scores differ significantly."""
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_task[r["task_id"]][r["agent_variant"]] = r

    differences = []
    for task_id, variants in by_task.items():
        if "baseline" in variants and "safe-aware" in variants:
            b = variants["baseline"]
            s = variants["safe-aware"]
            diff = s["safe_overall"] - b["safe_overall"]
            if abs(diff) >= 0.2:
                differences.append({
                    "task_id": task_id,
                    "domain": b["domain"],
                    "baseline_safe": b["safe_overall"],
                    "safe_aware_safe": s["safe_overall"],
                    "delta": diff,
                    "improvement": "safe-aware better" if diff > 0 else "baseline better",
                })
    return sorted(differences, key=lambda x: abs(x["delta"]), reverse=True)


SAFE_DIMENSIONS = ["scope", "anchored_decisions", "flow_integrity", "escalation", "safe_overall"]
PRIMARY_ENDPOINT = "safe_overall"
N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 42
ALPHA = 0.05


def _get_paired_scores(
    results: list[dict], domain: str | None = None
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Extract paired (baseline, safe-aware) score arrays per dimension.

    Returns dict mapping dimension name to (baseline_scores, safe_aware_scores).
    Validates that every task has exactly one result per variant.
    """
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        if domain and r["domain"] != domain:
            continue
        by_task[r["task_id"]][r["agent_variant"]] = r

    # Keep only fully paired tasks
    paired_tasks = sorted(
        tid for tid, v in by_task.items()
        if "baseline" in v and "safe-aware" in v
    )
    if not paired_tasks:
        return {}

    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for dim in SAFE_DIMENSIONS:
        baseline = np.array([by_task[t]["baseline"][dim] for t in paired_tasks])
        safe_aware = np.array([by_task[t]["safe-aware"][dim] for t in paired_tasks])
        out[dim] = (baseline, safe_aware)
    return out


def _rank_biserial_from_wilcoxon(
    diffs: np.ndarray,
) -> float | None:
    """Compute rank-biserial correlation for paired differences (matched-pairs r).

    r = (R+ - R-) / (R+ + R-), where R+/R- are rank sums of positive/negative diffs.
    """
    nonzero = diffs[diffs != 0]
    if len(nonzero) == 0:
        return None
    ranks = stats.rankdata(np.abs(nonzero))
    r_plus = ranks[nonzero > 0].sum()
    r_minus = ranks[nonzero < 0].sum()
    total = r_plus + r_minus
    if total == 0:
        return None
    return (r_plus - r_minus) / total


def _paired_test(
    baseline: np.ndarray, safe_aware: np.ndarray
) -> dict[str, Any]:
    """Run Wilcoxon signed-rank test with sign-test fallback for heavy ties."""
    diffs = safe_aware - baseline
    n_total = len(diffs)
    nonzero_diffs = diffs[diffs != 0]
    n_nonzero = len(nonzero_diffs)

    result: dict[str, Any] = {
        "n_pairs": n_total,
        "n_nonzero_pairs": n_nonzero,
        "mean_diff": float(np.mean(diffs)),
        "median_diff": float(np.median(diffs)),
        "baseline_mean": float(np.mean(baseline)),
        "safe_aware_mean": float(np.mean(safe_aware)),
    }

    # Need at least 6 nonzero pairs for Wilcoxon to be meaningful
    if n_nonzero >= 6:
        stat, p_value = stats.wilcoxon(
            baseline, safe_aware, alternative="two-sided", zero_method="wilcox"
        )
        result["test"] = "wilcoxon"
        result["statistic"] = float(stat)
        result["p_value"] = float(p_value)
        result["effect_size"] = _rank_biserial_from_wilcoxon(diffs)
        result["effect_size_type"] = "rank_biserial_r"
    elif n_nonzero >= 1:
        # Sign test fallback: count positive vs negative differences
        n_pos = int(np.sum(nonzero_diffs > 0))
        p_value = float(stats.binomtest(n_pos, n_nonzero, 0.5).pvalue)
        result["test"] = "sign_test"
        result["n_positive"] = n_pos
        result["n_negative"] = n_nonzero - n_pos
        result["p_value"] = float(p_value)
        result["effect_size"] = None
        result["effect_size_type"] = None
        result["note"] = "Too few nonzero pairs for Wilcoxon; sign test used"
    else:
        result["test"] = "none"
        result["p_value"] = None
        result["effect_size"] = None
        result["effect_size_type"] = None
        result["note"] = "All pairs tied — no test possible"

    return result


def _bootstrap_ci(
    baseline: np.ndarray,
    safe_aware: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
    alpha: float = ALPHA,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Bootstrap 95% CI for mean paired difference, resampling paired rows."""
    rng = np.random.default_rng(seed)
    diffs = safe_aware - baseline
    n = len(diffs)
    boot_means = np.array([
        rng.choice(diffs, size=n, replace=True).mean() for _ in range(n_boot)
    ])
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return lo, hi


def _stratified_bootstrap_ci(
    results: list[dict],
    dim: str,
    n_boot: int = N_BOOTSTRAP,
    alpha: float = ALPHA,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Stratified bootstrap CI for combined analysis, preserving domain balance."""
    rng = np.random.default_rng(seed)
    domain_pairs: dict[str, np.ndarray] = {}

    for domain in ["airline", "retail"]:
        pairs = _get_paired_scores(results, domain=domain)
        if dim in pairs:
            b, s = pairs[dim]
            domain_pairs[domain] = s - b

    if not domain_pairs:
        return (0.0, 0.0)

    boot_means = []
    for _ in range(n_boot):
        all_diffs = []
        for diffs in domain_pairs.values():
            idx = rng.integers(0, len(diffs), size=len(diffs))
            all_diffs.append(diffs[idx])
        combined = np.concatenate(all_diffs)
        boot_means.append(combined.mean())

    boot_means = np.array(boot_means)
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return lo, hi


def _apply_holm_correction(
    test_results: list[tuple[str, dict[str, Any]]]
) -> list[tuple[str, dict[str, Any]]]:
    """Apply Holm-Bonferroni correction to p-values. Marks primary endpoint."""
    # Separate primary from exploratory
    primary = [(label, r) for label, r in test_results if PRIMARY_ENDPOINT in label]
    exploratory = [(label, r) for label, r in test_results if PRIMARY_ENDPOINT not in label]

    # Apply Holm only to exploratory tests
    p_values = [r["p_value"] for _, r in exploratory if r.get("p_value") is not None]
    if p_values:
        n_tests = len(p_values)
        sorted_indices = np.argsort(p_values)
        p_idx = 0
        for rank, idx in enumerate(sorted_indices):
            label, r = exploratory[idx]
            if r.get("p_value") is not None:
                corrected = min(r["p_value"] * (n_tests - rank), 1.0)
                r["p_value_holm"] = corrected
                r["significant_holm"] = corrected < ALPHA
                p_idx += 1

    # Mark primary endpoint
    for label, r in primary:
        r["is_primary"] = True
        if r.get("p_value") is not None:
            r["significant"] = r["p_value"] < ALPHA

    return primary + exploratory


def run_statistical_analysis(results: list[dict]) -> dict[str, Any]:
    """Run full statistical analysis: paired tests, CIs, effect sizes."""
    analysis: dict[str, Any] = {"domains": {}, "combined": {}}

    # Per-domain analysis
    for domain in ["airline", "retail"]:
        pairs = _get_paired_scores(results, domain=domain)
        if not pairs:
            continue

        domain_results: dict[str, Any] = {}
        for dim in SAFE_DIMENSIONS:
            if dim not in pairs:
                continue
            b, s = pairs[dim]
            test_result = _paired_test(b, s)
            ci_lo, ci_hi = _bootstrap_ci(b, s)
            test_result["ci_95"] = (ci_lo, ci_hi)
            domain_results[dim] = test_result

        analysis["domains"][domain] = domain_results

    # Combined analysis (stratified bootstrap)
    combined_pairs = _get_paired_scores(results)
    if combined_pairs:
        combined_results: dict[str, Any] = {}
        for dim in SAFE_DIMENSIONS:
            if dim not in combined_pairs:
                continue
            b, s = combined_pairs[dim]
            test_result = _paired_test(b, s)
            ci_lo, ci_hi = _stratified_bootstrap_ci(results, dim)
            test_result["ci_95"] = (ci_lo, ci_hi)
            combined_results[dim] = test_result
        analysis["combined"] = combined_results

    # Collect all tests for Holm correction
    all_tests: list[tuple[str, dict[str, Any]]] = []
    for group_key, group_data in [("combined", analysis["combined"])] + [
        (f"domain_{d}", v) for d, v in analysis["domains"].items()
    ]:
        for dim, result in group_data.items():
            all_tests.append((f"{group_key}/{dim}", result))

    _apply_holm_correction(all_tests)
    return analysis


def print_statistical_analysis(analysis: dict[str, Any]) -> None:
    """Print statistical analysis results to console."""
    print("\n=== Statistical Analysis ===")
    print(f"Primary endpoint: {PRIMARY_ENDPOINT}")
    print(f"Multiple comparison correction: Holm-Bonferroni (exploratory tests)")
    print(f"Bootstrap CIs: {N_BOOTSTRAP} resamples, {int((1 - ALPHA) * 100)}% level\n")

    for group_label, group_key in [
        ("Combined (all domains)", "combined"),
        ("Airline", "domains"),
        ("Retail", "domains"),
    ]:
        if group_key == "domains":
            domain = group_label.lower()
            data = analysis.get("domains", {}).get(domain, {})
        else:
            data = analysis.get(group_key, {})

        if not data:
            continue

        print(f"--- {group_label} ---")
        print(
            f"{'dimension':<22} {'test':<10} {'n':>3} {'mean_diff':>9} "
            f"{'CI_lo':>7} {'CI_hi':>7} {'p':>8} {'p_holm':>8} {'r':>6} {'sig':>4}"
        )
        print("-" * 100)

        for dim in SAFE_DIMENSIONS:
            if dim not in data:
                continue
            r = data[dim]
            p_str = f"{r['p_value']:.4f}" if r.get("p_value") is not None else "   n/a"
            p_holm = r.get("p_value_holm")
            p_holm_str = f"{p_holm:.4f}" if p_holm is not None else "   n/a"
            eff = r.get("effect_size")
            eff_str = f"{eff:.3f}" if eff is not None else "  n/a"
            ci = r.get("ci_95", (0, 0))

            # Determine significance marker
            is_primary = r.get("is_primary", False)
            if is_primary:
                sig = "* " if r.get("significant") else "  "
            else:
                sig = "* " if r.get("significant_holm") else "  "

            dim_label = dim + (" (P)" if is_primary else "")
            print(
                f"{dim_label:<22} {r.get('test', 'n/a'):<10} "
                f"{r['n_nonzero_pairs']:>3} {r['mean_diff']:>+9.4f} "
                f"{ci[0]:>+7.4f} {ci[1]:>+7.4f} {p_str:>8} {p_holm_str:>8} "
                f"{eff_str:>6} {sig:>4}"
            )
        print()


def generate_statistical_report(
    analysis: dict[str, Any], output_path: Path
) -> None:
    """Write statistical_analysis.md report."""
    lines = [
        "# Statistical Analysis Report\n",
        "## Methodology\n",
        f"- **Primary endpoint**: `{PRIMARY_ENDPOINT}` (confirmatory, α={ALPHA})",
        "- **Exploratory endpoints**: per-dimension scores (Holm-Bonferroni corrected)",
        "- **Paired test**: Wilcoxon signed-rank (≥6 nonzero pairs) or sign test (fallback)",
        "- **Effect size**: rank-biserial correlation (r) for Wilcoxon results",
        f"- **Confidence intervals**: bootstrap ({N_BOOTSTRAP} resamples), "
        f"{int((1 - ALPHA) * 100)}% level",
        "- **Combined CI**: stratified bootstrap preserving domain balance (15/15)",
        "- **Zero differences**: excluded from Wilcoxon (Pratt's method: `zero_method='wilcox'`)\n",
        "## Interpretation Guide\n",
        "- **mean_diff > 0**: safe-aware agent scores higher (improvement)",
        "- **mean_diff < 0**: baseline agent scores higher",
        "- **r ∈ [-1, 1]**: rank-biserial effect size; |r| > 0.5 is large",
        "- **(P)**: primary endpoint (uncorrected α); others use Holm correction",
        "- **\\***: statistically significant at α=0.05\n",
    ]

    for group_label, group_key in [
        ("Combined (All Domains)", "combined"),
        ("Airline Domain", "airline"),
        ("Retail Domain", "retail"),
    ]:
        data = (
            analysis.get(group_key, {})
            if group_key == "combined"
            else analysis.get("domains", {}).get(group_key, {})
        )
        if not data:
            continue

        lines.append(f"## {group_label}\n")
        lines.append(
            "| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |"
        )
        lines.append(
            "|-----------|------|----|--------|--------|---|----------|---|-----|"
        )

        for dim in SAFE_DIMENSIONS:
            if dim not in data:
                continue
            r = data[dim]
            p_str = f"{r['p_value']:.4f}" if r.get("p_value") is not None else "n/a"
            p_holm = r.get("p_value_holm")
            p_holm_str = f"{p_holm:.4f}" if p_holm is not None else "—"
            eff = r.get("effect_size")
            eff_str = f"{eff:.3f}" if eff is not None else "—"
            ci = r.get("ci_95", (0, 0))
            ci_str = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]"

            is_primary = r.get("is_primary", False)
            if is_primary:
                sig = "✱" if r.get("significant") else ""
            else:
                sig = "✱" if r.get("significant_holm") else ""

            dim_label = f"**{dim}** (P)" if is_primary else dim
            note = r.get("note", "")
            test_label = r.get("test", "n/a")
            if note:
                test_label += f" †"

            lines.append(
                f"| {dim_label} | {test_label} | {r['n_nonzero_pairs']} | "
                f"{r['mean_diff']:+.4f} | {ci_str} | {p_str} | {p_holm_str} | "
                f"{eff_str} | {sig} |"
            )

        lines.append("")
        lines.append(f"*n\\* = nonzero pairs (ties excluded)*\n")

        # Add notes for any dimension with special handling
        notes = []
        for dim in SAFE_DIMENSIONS:
            if dim in data and data[dim].get("note"):
                notes.append(f"- **{dim}**: {data[dim]['note']}")
        if notes:
            lines.append("**Notes:**")
            lines.extend(notes)
            lines.append("")

    # Key findings summary
    lines.append("## Key Findings\n")

    combined = analysis.get("combined", {})
    primary = combined.get(PRIMARY_ENDPOINT, {})
    if primary:
        p = primary.get("p_value")
        diff = primary.get("mean_diff", 0)
        direction = "higher" if diff > 0 else "lower"
        ci = primary.get("ci_95", (0, 0))
        lines.append(
            f"1. **Primary endpoint ({PRIMARY_ENDPOINT})**: "
            f"Safe-aware agent scores {direction} by {abs(diff):.3f} on average "
            f"(95% CI: [{ci[0]:+.3f}, {ci[1]:+.3f}])"
        )
        if p is not None:
            sig_text = "statistically significant" if p < ALPHA else "not statistically significant"
            lines.append(f"   - Wilcoxon p={p:.4f} ({sig_text} at α={ALPHA})")

    # Per-domain highlights
    finding_num = 2
    for domain in ["airline", "retail"]:
        domain_data = analysis.get("domains", {}).get(domain, {})
        primary_d = domain_data.get(PRIMARY_ENDPOINT, {})
        if primary_d:
            diff = primary_d.get("mean_diff", 0)
            direction = "improvement" if diff > 0 else "regression"
            lines.append(
                f"{finding_num}. **{domain.title()}**: {direction} of {abs(diff):.3f} in overall SAFE score"
            )
            # Find largest effect
            best_dim = max(
                (d for d in SAFE_DIMENSIONS if d in domain_data and d != PRIMARY_ENDPOINT),
                key=lambda d: abs(domain_data[d].get("mean_diff", 0)),
                default=None,
            )
            if best_dim:
                bd = domain_data[best_dim]
                eff = bd.get("effect_size")
                eff_str = f"r={eff:.3f}" if eff is not None else "sign test (ties too frequent for effect size)"
                lines.append(
                    f"   - Largest effect in **{best_dim}**: "
                    f"Δ={bd['mean_diff']:+.3f}, {eff_str}"
                )
            finding_num += 1

    lines.append("")
    lines.append("## Limitations\n")
    lines.append(
        f"- Small sample size (n=15 per domain) limits statistical power"
    )
    lines.append(
        "- Binary dimensions (scope, escalation) produce many ties, "
        "reducing effective sample for Wilcoxon"
    )
    lines.append(
        "- Results should be interpreted as exploratory evidence, "
        "not definitive proof of effect"
    )
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Statistical analysis written to {output_path}")


def generate_paper_examples(results: list[dict], traces_dir: Path, output_path: Path) -> None:
    """Generate paper_examples.md with curated examples."""
    divergences = find_divergence_cases(results)
    differences = find_variant_differences(results)

    lines = [
        "# Paper Examples\n",
        "Selected examples from the SAFE benchmark experiment.\n",
    ]

    if differences:
        lines.append("## Variant Comparison Examples\n")
        lines.append("Cases where baseline and SAFE-aware agents behaved differently:\n")
        for d in differences[:5]:
            lines.append(f"### {d['task_id']} ({d['domain']})\n")
            lines.append(f"- **Baseline SAFE score**: {d['baseline_safe']:.2f}")
            lines.append(f"- **SAFE-aware SAFE score**: {d['safe_aware_safe']:.2f}")
            lines.append(f"- **Delta**: {d['delta']:+.2f} ({d['improvement']})")
            lines.append("")

    if divergences:
        lines.append("## Divergence Cases\n")
        lines.append("Cases where task success and SAFE compliance diverge:\n")
        for d in divergences[:5]:
            lines.append(f"### {d['task_id']} ({d['domain']}, {d['agent_variant']})\n")
            lines.append(f"- **Type**: {d['divergence_type']}")
            lines.append(f"- **SAFE overall**: {d['safe_overall']:.2f}")
            lines.append(f"- **Task completed**: {d.get('task_completed')}")
            lines.append(f"- **Note**: {d['note']}")
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Paper examples written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze SAFE benchmark results")
    parser.add_argument("--run-dir", help="Path to a specific run directory")
    parser.add_argument("--latest", action="store_true", help="Use the latest run")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    if args.run_dir:
        run_dir = Path(args.run_dir)
    elif args.latest:
        run_dir = find_latest_run(project_root / "outputs")
        if not run_dir:
            print("No runs found in outputs/runs/")
            sys.exit(1)
    else:
        run_dir = find_latest_run(project_root / "outputs")
        if not run_dir:
            print("No runs found. Specify --run-dir or run the experiment first.")
            sys.exit(1)

    results_path = run_dir / "results.json"
    if not results_path.exists():
        print(f"No results.json found in {run_dir}")
        sys.exit(1)

    print(f"Analyzing: {run_dir}")
    results = load_results(results_path)
    print(f"Loaded {len(results)} results")

    print_comparison_table(results)
    print_per_task_table(results)

    # Divergence analysis
    divergences = find_divergence_cases(results)
    if divergences:
        print(f"\n=== Divergence Cases ({len(divergences)}) ===")
        for d in divergences:
            print(f"  {d['task_id']} ({d['agent_variant']}): {d['note']}")

    # Variant differences
    differences = find_variant_differences(results)
    if differences:
        print(f"\n=== Significant Variant Differences ({len(differences)}) ===")
        for d in differences:
            print(f"  {d['task_id']}: delta={d['delta']:+.2f} ({d['improvement']})")

    # Statistical analysis
    analysis = run_statistical_analysis(results)
    print_statistical_analysis(analysis)

    # Generate reports
    reports_dir = project_root / "outputs" / "reports"
    generate_statistical_report(analysis, reports_dir / "statistical_analysis.md")
    generate_paper_examples(results, run_dir / "traces", reports_dir / "paper_examples.md")


if __name__ == "__main__":
    main()
