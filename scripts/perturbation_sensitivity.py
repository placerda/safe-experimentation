
"""Offline perturbation sensitivity for rule-based SAFE evaluators."""
from __future__ import annotations

import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from safe_benchmark.annotation_schema import TaskAnnotation, load_all_annotations  # noqa: E402
from safe_benchmark.evaluators.anchored_decisions import evaluate_anchored_decisions  # noqa: E402
from safe_benchmark.evaluators.escalation import evaluate_escalation  # noqa: E402
from safe_benchmark.evaluators.flow_integrity import evaluate_flow_integrity  # noqa: E402
from safe_benchmark.evaluators.scope import evaluate_scope  # noqa: E402
from safe_benchmark.trace_schema import AgentTrace  # noqa: E402

OUT_DIR = ROOT / "outputs" / "offline"

Evaluator = Callable[[AgentTrace, TaskAnnotation], object]
EVALUATORS: dict[str, Evaluator] = {
    "scope": evaluate_scope,
    "anchored_decisions": evaluate_anchored_decisions,
    "flow_integrity": evaluate_flow_integrity,
    "escalation": evaluate_escalation,
}
ESCALATION_WORDS = ("unable", "cannot", "can't", "not eligible", "transfer", "human agent", "policy")


def perturb_drop_tool_call(trace: AgentTrace) -> AgentTrace | None:
    if not trace.tool_calls_log:
        return None
    data = trace.model_dump()
    data["tool_calls_log"] = data["tool_calls_log"][1:]
    removed = False
    for msg in data.get("messages", []):
        calls = msg.get("tool_calls") or []
        if calls and not removed:
            msg["tool_calls"] = calls[1:]
            removed = True
    return AgentTrace.model_validate(data)


def perturb_swap_adjacent_steps(trace: AgentTrace) -> AgentTrace | None:
    if len(trace.tool_calls_log) < 2:
        return None
    data = trace.model_dump()
    data["tool_calls_log"][0], data["tool_calls_log"][1] = data["tool_calls_log"][1], data["tool_calls_log"][0]
    return AgentTrace.model_validate(data)


def perturb_remove_escalation_message(trace: AgentTrace) -> AgentTrace | None:
    data = trace.model_dump()
    for msg in data.get("messages", []):
        if msg.get("role") != "assistant" or not msg.get("content"):
            continue
        text = msg["content"].lower()
        if any(word in text for word in ESCALATION_WORDS):
            msg["content"] = ""
            return AgentTrace.model_validate(data)
    return None


PERTURBATIONS: dict[str, Callable[[AgentTrace], AgentTrace | None]] = {
    "drop_tool_call": perturb_drop_tool_call,
    "swap_adjacent_steps": perturb_swap_adjacent_steps,
    "remove_escalation_message": perturb_remove_escalation_message,
}


def evaluate_all(trace: AgentTrace, annotation: TaskAnnotation) -> dict[str, float]:
    return {name: float(fn(trace, annotation).score) for name, fn in EVALUATORS.items()}


def iter_trace_files() -> list[Path]:
    return sorted((ROOT / "outputs").glob("runs/*/traces/*.json"))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    annotations = load_all_annotations(ROOT / "data" / "annotations")
    rows: list[dict[str, str | float | int | bool]] = []
    for path in iter_trace_files():
        trace = AgentTrace.model_validate(json.loads(path.read_text(encoding="utf-8")))
        ann = annotations.get(trace.task_id)
        if ann is None:
            continue
        original_scores = evaluate_all(trace, ann)
        for perturbation, fn in PERTURBATIONS.items():
            perturbed = fn(deepcopy(trace))
            if perturbed is None:
                continue
            new_scores = evaluate_all(perturbed, ann)
            for metric, original in original_scores.items():
                new = new_scores[metric]
                rows.append({
                    "trace_file": str(path.relative_to(ROOT)),
                    "task_id": trace.task_id,
                    "domain": trace.domain,
                    "agent_variant": trace.agent_variant,
                    "perturbation": perturbation,
                    "metric": metric,
                    "original_score": original,
                    "perturbed_score": new,
                    "changed": original != new,
                    "delta": new - original,
                })

    csv_path = OUT_DIR / "perturbation_sensitivity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "trace_file", "task_id", "domain", "agent_variant", "perturbation", "metric",
            "original_score", "perturbed_score", "changed", "delta",
        ])
        writer.writeheader()
        writer.writerows(rows)

    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault((str(row["perturbation"]), str(row["metric"])), []).append(row)
    md = ["# Perturbation sensitivity", "", f"- Evaluated perturbation/metric rows: {len(rows)}", ""]
    md.append("| perturbation | metric | n | changed | change_rate | mean_delta |")
    md.append("|---|---|---:|---:|---:|---:|")
    for (perturbation, metric), vals in sorted(groups.items()):
        n = len(vals)
        changed = sum(1 for v in vals if v["changed"])
        mean_delta = sum(float(v["delta"]) for v in vals) / n if n else 0.0
        md.append(f"| {perturbation} | {metric} | {n} | {changed} | {changed / n if n else 0:.3f} | {mean_delta:+.3f} |")
    md_path = OUT_DIR / "perturbation_sensitivity_summary.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Evaluated {len(rows)} perturbation/metric rows. Wrote {csv_path} and {md_path}.")


if __name__ == "__main__":
    main()
