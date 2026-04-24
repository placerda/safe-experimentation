"""Reporting — aggregates per-task results into summary tables and reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from safe_benchmark.evaluators.base import EvaluatorResult


def compute_safe_overall(results: dict[str, EvaluatorResult]) -> float:
    """Compute overall SAFE score as average of four dimensions."""
    if not results:
        return 0.0
    return sum(r.score for r in results.values()) / len(results)


def format_results_table(all_results: list[dict[str, Any]]) -> str:
    """Format results as a markdown table.

    Each entry in all_results should have:
    - task_id, domain, agent_variant
    - scope, anchored_decisions, flow_integrity, escalation (scores)
    - safe_overall
    """
    header = "| domain | agent_variant | task_id | scope | anchored | flow | escalation | safe_overall |"
    separator = "|--------|--------------|---------|-------|----------|------|------------|--------------|"
    rows = [header, separator]

    for r in sorted(all_results, key=lambda x: (x["domain"], x["agent_variant"], x["task_id"])):
        row = (
            f"| {r['domain']} | {r['agent_variant']} | {r['task_id']} "
            f"| {r['scope']:.2f} | {r['anchored_decisions']:.2f} "
            f"| {r['flow_integrity']:.2f} | {r['escalation']:.2f} "
            f"| {r['safe_overall']:.2f} |"
        )
        rows.append(row)

    return "\n".join(rows)


def format_aggregate_table(all_results: list[dict[str, Any]]) -> str:
    """Format aggregate scores by domain and agent variant."""
    from collections import defaultdict

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in all_results:
        key = (r["domain"], r["agent_variant"])
        groups[key].append(r)

    header = "| domain | agent_variant | n | scope | anchored | flow | escalation | safe_overall |"
    separator = "|--------|--------------|---|-------|----------|------|------------|--------------|"
    rows = [header, separator]

    for (domain, variant), items in sorted(groups.items()):
        n = len(items)
        avg = lambda key: sum(r[key] for r in items) / n
        row = (
            f"| {domain} | {variant} | {n} "
            f"| {avg('scope'):.2f} | {avg('anchored_decisions'):.2f} "
            f"| {avg('flow_integrity'):.2f} | {avg('escalation'):.2f} "
            f"| {avg('safe_overall'):.2f} |"
        )
        rows.append(row)

    return "\n".join(rows)


def generate_report(all_results: list[dict[str, Any]], output_path: Path) -> None:
    """Generate a markdown report with per-task and aggregate results."""
    lines = [
        "# SAFE Benchmark Report\n",
        "## Aggregate Results\n",
        format_aggregate_table(all_results),
        "\n## Per-Task Results\n",
        format_results_table(all_results),
        "\n## Methodology\n",
        "- **Scope**: Checked allowed/disallowed tool usage",
        "- **Anchored Decisions**: Verified evidence-based decisions, no forbidden assumptions",
        "- **Flow Integrity**: Validated step ordering",
        "- **Escalation**: Checked for appropriate escalation behavior",
        f"\n*{len(all_results)} task-agent evaluations total.*\n",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def save_results_json(all_results: list[dict[str, Any]], output_path: Path) -> None:
    """Save raw results as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
