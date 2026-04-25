"""Enrich paper_examples.md with actual trace excerpts and visualizations.

Builds:
- outputs/reports/paper_examples.md  (with trace excerpts side-by-side)
- outputs/reports/figures/*.png       (paired plots, deltas, dimension breakdowns)

Usage:
    python scripts/enrich_paper_examples.py [--run-dir outputs/runs/<run-id>] [--latest]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SAFE_DIMENSIONS = ["scope", "anchored_decisions", "flow_integrity", "escalation"]
MAX_MESSAGES_EXCERPT = 8
MAX_CONTENT_LEN = 280


def find_latest_run(output_dir: Path) -> Path | None:
    runs_dir = output_dir / "runs"
    if not runs_dir.exists():
        return None
    runs = sorted(runs_dir.iterdir(), reverse=True)
    return runs[0] if runs else None


def load_trace(traces_dir: Path, variant: str, task_id: str) -> dict | None:
    path = traces_dir / f"{variant}_{task_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def truncate(text: str, n: int = MAX_CONTENT_LEN) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= n:
        return text
    return text[: n - 3] + "..."


def format_messages_excerpt(messages: list[dict], max_msgs: int = MAX_MESSAGES_EXCERPT) -> str:
    """Format first N messages as a markdown blockquote conversation."""
    lines = []
    for msg in messages[:max_msgs]:
        role = msg.get("role", "?").upper()
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []
        if content:
            lines.append(f"> **{role}**: {truncate(content)}")
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    name = tc.get("function", {}).get("name") or tc.get("name", "?")
                    lines.append(f"> **{role}** _calls tool_: `{name}`")
    if len(messages) > max_msgs:
        lines.append(f"> _... ({len(messages) - max_msgs} more turns omitted)_")
    return "\n".join(lines)


def format_tool_calls(tool_calls_log: list[dict]) -> str:
    """Format a compact list of tool calls used in the trace."""
    if not tool_calls_log:
        return "_(no tool calls)_"
    lines = []
    for i, tc in enumerate(tool_calls_log, 1):
        name = tc.get("name", "?")
        args = tc.get("arguments", {})
        args_str = ", ".join(f"{k}={v!r}" for k, v in list(args.items())[:3])
        if len(args) > 3:
            args_str += ", ..."
        lines.append(f"{i}. `{name}({truncate(args_str, 120)})`")
    return "\n".join(lines)


def get_eval_summary(result: dict) -> str:
    """Format SAFE evaluator scores + reasons compactly."""
    parts = []
    for dim in SAFE_DIMENSIONS:
        score = result.get(dim, 0)
        reason = result.get(f"{dim}_reason", "")
        passed = result.get(f"{dim}_passed", False)
        marker = "✓" if passed else "✗"
        parts.append(f"- **{dim}** ({score:.2f}) {marker}: {truncate(reason, 200)}")
    return "\n".join(parts)


def build_comparison_section(
    task_id: str,
    domain: str,
    baseline: dict,
    safe_aware: dict,
    traces_dir: Path,
) -> list[str]:
    """Build a detailed comparison section for one task."""
    lines = [f"### {task_id} ({domain})\n"]
    lines.append(
        f"- **Baseline SAFE**: {baseline['safe_overall']:.2f}  |  "
        f"**Safe-aware SAFE**: {safe_aware['safe_overall']:.2f}  |  "
        f"**Δ**: {safe_aware['safe_overall'] - baseline['safe_overall']:+.2f}"
    )
    lines.append(
        f"- **Task completed**: baseline={baseline.get('task_completed')} | "
        f"safe-aware={safe_aware.get('task_completed')}"
    )

    # Per-dimension table
    lines.append("\n| Dimension | Baseline | Safe-aware | Δ |")
    lines.append("|-----------|----------|------------|---|")
    for dim in SAFE_DIMENSIONS:
        b = baseline.get(dim, 0)
        s = safe_aware.get(dim, 0)
        delta = s - b
        marker = " 🟢" if delta > 0 else (" 🔴" if delta < 0 else "")
        lines.append(f"| {dim} | {b:.2f} | {s:.2f} | {delta:+.2f}{marker} |")
    lines.append("")

    # Load traces
    b_trace = load_trace(traces_dir, "baseline", task_id)
    s_trace = load_trace(traces_dir, "safe-aware", task_id)

    if b_trace and s_trace:
        lines.append("#### Tool calls comparison\n")
        lines.append("**Baseline**:")
        lines.append(format_tool_calls(b_trace.get("tool_calls_log", [])))
        lines.append("\n**Safe-aware**:")
        lines.append(format_tool_calls(s_trace.get("tool_calls_log", [])))
        lines.append("")

        # Show evaluator details for the dimension with biggest divergence
        biggest_diff_dim = max(
            SAFE_DIMENSIONS,
            key=lambda d: abs(safe_aware.get(d, 0) - baseline.get(d, 0)),
        )
        if abs(safe_aware.get(biggest_diff_dim, 0) - baseline.get(biggest_diff_dim, 0)) > 0:
            lines.append(f"#### Why the {biggest_diff_dim} score differs\n")
            lines.append(
                f"- **Baseline**: {truncate(baseline.get(f'{biggest_diff_dim}_reason', ''), 300)}"
            )
            lines.append(
                f"- **Safe-aware**: {truncate(safe_aware.get(f'{biggest_diff_dim}_reason', ''), 300)}"
            )
            lines.append("")

        # Show conversation excerpt for the variant with HIGHER score (more interesting behavior)
        better_variant, better_trace = (
            ("Safe-aware", s_trace)
            if safe_aware["safe_overall"] >= baseline["safe_overall"]
            else ("Baseline", b_trace)
        )
        lines.append(f"#### Conversation excerpt ({better_variant})\n")
        lines.append(format_messages_excerpt(better_trace.get("messages", [])))
        lines.append("")

    return lines


def build_divergence_section(result: dict, traces_dir: Path) -> list[str]:
    """Build section for a divergence case (task success but SAFE failure)."""
    task_id = result["task_id"]
    variant = result["agent_variant"]
    lines = [f"### {task_id} ({result['domain']}, {variant})\n"]
    lines.append(
        f"- **SAFE overall**: {result['safe_overall']:.2f}  |  "
        f"**Task completed**: {result.get('task_completed')}"
    )
    lines.append("\n**SAFE evaluator findings:**\n")
    lines.append(get_eval_summary(result))
    lines.append("")

    trace = load_trace(traces_dir, variant, task_id)
    if trace:
        lines.append("**Tool calls used:**\n")
        lines.append(format_tool_calls(trace.get("tool_calls_log", [])))
        lines.append("")

    return lines


def build_paper_examples(results: list[dict], traces_dir: Path, output_path: Path) -> None:
    """Build enriched paper_examples.md."""
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_task[r["task_id"]][r["agent_variant"]] = r

    # Sort cases by absolute SAFE delta
    differences = []
    for task_id, variants in by_task.items():
        if "baseline" in variants and "safe-aware" in variants:
            b = variants["baseline"]
            s = variants["safe-aware"]
            differences.append((task_id, b, s, s["safe_overall"] - b["safe_overall"]))

    differences.sort(key=lambda x: abs(x[3]), reverse=True)

    # Find divergence cases
    divergences = [
        r for r in results
        if r.get("task_completed") and r["safe_overall"] < 0.5
    ]
    divergences.sort(key=lambda r: r["safe_overall"])

    lines = [
        "# Paper Examples — Detailed Trace Analysis\n",
        "Curated examples from the SAFE benchmark experiment, with conversation excerpts, "
        "tool call traces, and evaluator findings.\n",
        "## Table of Contents\n",
        "- [Top Variant Differences](#top-variant-differences)",
        "- [Divergence Cases (Task Success but SAFE Failure)](#divergence-cases)",
        "",
    ]

    # Top variant differences (significant ones, |delta| >= 0.20)
    significant_diffs = [d for d in differences if abs(d[3]) >= 0.2]
    if significant_diffs:
        lines.append("## Top Variant Differences\n")
        lines.append(
            "Tasks where baseline and safe-aware agents diverged by ≥0.20 in SAFE overall score. "
            "These illustrate the qualitative differences between the two prompting strategies.\n"
        )
        for task_id, b, s, delta in significant_diffs[:6]:
            lines.extend(
                build_comparison_section(task_id, b["domain"], b, s, traces_dir)
            )
            lines.append("---\n")

    # Divergence cases
    if divergences:
        lines.append("## Divergence Cases\n")
        lines.append(
            "Tasks where the agent **completed the task successfully but violated SAFE constraints**. "
            "These are the central evidence that *task success ≠ responsible behavior*.\n"
        )
        for r in divergences[:6]:
            lines.extend(build_divergence_section(r, traces_dir))
            lines.append("---\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Paper examples written to {output_path}")


# ---------------- Visualizations ----------------

def plot_paired_dots(results: list[dict], output_path: Path) -> None:
    """Slope chart showing each task's baseline -> safe-aware SAFE score."""
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_task[r["task_id"]][r["agent_variant"]] = r

    fig, axes = plt.subplots(1, 2, figsize=(11, 6), sharey=True)

    for ax, domain in zip(axes, ["airline", "retail"]):
        tasks = sorted(t for t, v in by_task.items()
                       if "baseline" in v and "safe-aware" in v
                       and v["baseline"]["domain"] == domain)
        for task_id in tasks:
            b = by_task[task_id]["baseline"]["safe_overall"]
            s = by_task[task_id]["safe-aware"]["safe_overall"]
            color = "#2ca02c" if s > b else ("#d62728" if s < b else "#7f7f7f")
            ax.plot([0, 1], [b, s], color=color, alpha=0.6, marker="o", markersize=5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["baseline", "safe-aware"])
        ax.set_title(f"{domain.title()} (n={len(tasks)})")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, axis="y", alpha=0.3)
        ax.axhline(0.75, color="black", linestyle="--", alpha=0.3, label="pass threshold")

    axes[0].set_ylabel("SAFE overall score")
    fig.suptitle("Per-task SAFE scores: baseline vs safe-aware\n(green=improvement, red=regression, gray=tie)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Paired dots plot saved to {output_path}")


def plot_dimension_breakdown(results: list[dict], output_path: Path) -> None:
    """Grouped bar chart of mean scores per dimension/domain/variant."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in results:
        groups[(r["domain"], r["agent_variant"])].append(r)

    domains = ["airline", "retail"]
    variants = ["baseline", "safe-aware"]
    colors = {"baseline": "#1f77b4", "safe-aware": "#ff7f0e"}

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    x = np.arange(len(SAFE_DIMENSIONS))
    width = 0.35

    for ax, domain in zip(axes, domains):
        for i, variant in enumerate(variants):
            means = [
                np.mean([r[dim] for r in groups[(domain, variant)]])
                for dim in SAFE_DIMENSIONS
            ]
            ax.bar(x + (i - 0.5) * width, means, width, label=variant, color=colors[variant])
        ax.set_xticks(x)
        ax.set_xticklabels([d.replace("_", "\n") for d in SAFE_DIMENSIONS])
        ax.set_title(domain.title())
        ax.set_ylim(0, 1.05)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(loc="lower right")

    axes[0].set_ylabel("Mean score")
    fig.suptitle("SAFE dimension scores by domain and agent variant")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Dimension breakdown saved to {output_path}")


def plot_delta_distribution(results: list[dict], output_path: Path) -> None:
    """Histogram of per-task SAFE deltas (safe-aware - baseline)."""
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_task[r["task_id"]][r["agent_variant"]] = r

    deltas_by_domain: dict[str, list[float]] = defaultdict(list)
    for task_id, variants in by_task.items():
        if "baseline" in variants and "safe-aware" in variants:
            d = variants["safe-aware"]["safe_overall"] - variants["baseline"]["safe_overall"]
            deltas_by_domain[variants["baseline"]["domain"]].append(d)

    fig, ax = plt.subplots(figsize=(10, 5))
    bins = np.linspace(-0.6, 0.6, 25)
    colors = {"airline": "#1f77b4", "retail": "#ff7f0e"}
    for domain, deltas in deltas_by_domain.items():
        ax.hist(deltas, bins=bins, alpha=0.6, label=f"{domain} (n={len(deltas)})",
                color=colors.get(domain))
        ax.axvline(np.mean(deltas), color=colors.get(domain), linestyle="--",
                   alpha=0.8, label=f"{domain} mean={np.mean(deltas):+.3f}")

    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Δ SAFE overall (safe-aware − baseline)")
    ax.set_ylabel("Count of tasks")
    ax.set_title("Distribution of per-task SAFE score deltas")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Delta distribution saved to {output_path}")


def plot_divergence_scatter(results: list[dict], output_path: Path) -> None:
    """Scatter of task_completed vs SAFE score, highlighting divergence cases."""
    fig, ax = plt.subplots(figsize=(9, 6))

    rng = np.random.default_rng(42)
    for variant, marker, color in [("baseline", "o", "#1f77b4"), ("safe-aware", "s", "#ff7f0e")]:
        xs = []
        ys = []
        for r in results:
            if r["agent_variant"] == variant:
                # jitter task_completed
                tc = 1 if r.get("task_completed") else 0
                xs.append(tc + rng.uniform(-0.08, 0.08))
                ys.append(r["safe_overall"])
        ax.scatter(xs, ys, marker=marker, alpha=0.6, label=variant, color=color, s=80)

    ax.axhline(0.5, color="red", linestyle="--", alpha=0.5, label="SAFE failure threshold (0.5)")
    ax.axhline(0.75, color="green", linestyle="--", alpha=0.5, label="SAFE pass threshold (0.75)")

    # Highlight divergence quadrant
    ax.fill_between([0.5, 1.5], 0, 0.5, color="red", alpha=0.08, label="divergence zone")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["task failed", "task completed"])
    ax.set_ylabel("SAFE overall score")
    ax.set_title("Task completion vs SAFE compliance\n(red zone = task success but SAFE failure)")
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Divergence scatter saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", help="Path to specific run directory")
    parser.add_argument("--latest", action="store_true", help="Use latest run")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        run_dir = find_latest_run(project_root / "outputs")
        if not run_dir:
            print("No runs found")
            sys.exit(1)

    results_path = run_dir / "results.json"
    traces_dir = run_dir / "traces"
    if not results_path.exists():
        print(f"No results.json at {results_path}")
        sys.exit(1)

    with open(results_path) as f:
        results = json.load(f)

    print(f"Loaded {len(results)} results from {run_dir}")

    reports_dir = project_root / "outputs" / "reports"
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Build enriched markdown
    build_paper_examples(results, traces_dir, reports_dir / "paper_examples.md")

    # Build figures
    plot_paired_dots(results, figures_dir / "paired_scores.png")
    plot_dimension_breakdown(results, figures_dir / "dimension_breakdown.png")
    plot_delta_distribution(results, figures_dir / "delta_distribution.png")
    plot_divergence_scatter(results, figures_dir / "divergence_scatter.png")

    print("\nAll outputs generated successfully.")


if __name__ == "__main__":
    main()
