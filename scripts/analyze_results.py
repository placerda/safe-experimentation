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

    # Generate paper examples
    reports_dir = project_root / "outputs" / "reports"
    generate_paper_examples(results, run_dir / "traces", reports_dir / "paper_examples.md")


if __name__ == "__main__":
    main()
