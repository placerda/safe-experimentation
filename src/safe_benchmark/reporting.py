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


def format_safety_table(all_results: list[dict[str, Any]]) -> str:
    """Format outcome-level safety metrics (annotation-independent) by domain and variant."""
    from collections import defaultdict

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in all_results:
        groups[(r["domain"], r["agent_variant"])].append(r)

    header = (
        "| domain | agent_variant | n | tau2 | unsafe_write_rate | commission_rate (zero-write) "
        "| executed_writes | blocked_calls | transfer_rate | unconfirmed_w | unauth_w | retry_loops |"
    )
    separator = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    rows = [header, separator]

    def _mean(items: list[dict], key: str) -> float:
        vals = [float(r.get(key) or 0) for r in items]
        return sum(vals) / len(vals) if vals else 0.0

    for (domain, variant), items in sorted(groups.items()):
        n = len(items)
        tau_vals = [r["tau2_reward"] for r in items if r.get("tau2_reward") is not None]
        tau = sum(tau_vals) / len(tau_vals) if tau_vals else float("nan")
        zero = [r for r in items if r.get("zero_write_task")]
        commission = (
            f"{sum(1 for r in zero if r.get('commission_error')) / len(zero):.2f} (n={len(zero)})"
            if zero
            else "n/a"
        )
        rows.append(
            f"| {domain} | {variant} | {n} | {tau:.2f} "
            f"| {sum(1 for r in items if r.get('any_unsafe_write')) / n:.2f} "
            f"| {commission} "
            f"| {_mean(items, 'executed_writes'):.2f} | {_mean(items, 'blocked_calls'):.2f} "
            f"| {sum(1 for r in items if r.get('transferred')) / n:.2f} "
            f"| {_mean(items, 'unconfirmed_writes'):.2f} | {_mean(items, 'unauthenticated_writes'):.2f} "
            f"| {_mean(items, 'retry_loops'):.2f} |"
        )

    return "\n".join(rows)


def generate_report(all_results: list[dict[str, Any]], output_path: Path) -> None:
    """Generate a markdown report with per-task and aggregate results."""
    lines = [
        "# SAFE Benchmark Report\n",
        "## Aggregate Results\n",
        format_aggregate_table(all_results),
        "\n## Outcome-Level Safety Metrics\n",
        format_safety_table(all_results),
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
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def save_results_json(all_results: list[dict[str, Any]], output_path: Path) -> None:
    """Save raw results as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
