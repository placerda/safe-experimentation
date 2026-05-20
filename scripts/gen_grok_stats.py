"""Generate grok_stats.json and grok_stats.md in outputs/reports/."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RUNS = {
    "grok-3":      ROOT / "outputs/runs/20260519_152221__grok-3/results.json",
    "grok-3-mini": ROOT / "outputs/runs/20260519_152221__grok-3-mini/results.json",
}

DIMS = ["scope", "anchored_decisions", "flow_integrity", "escalation", "safe_overall"]
VARIANTS = ["baseline", "prompt-only", "safe-aware", "binding-only"]
DOMAINS = ["airline", "retail", "telecom"]


def compute_means(rows):
    by_dv = defaultdict(list)
    for r in rows:
        by_dv[(r["domain"], r["agent_variant"])].append(r)

    out = {}
    for (domain, variant), group in sorted(by_dv.items()):
        entry = {"n": len(group)}
        for d in DIMS:
            vals = [r[d] for r in group if r.get(d) is not None]
            entry[d] = round(sum(vals) / len(vals), 4) if vals else None
        t2 = [r["tau2_reward"] for r in group if r.get("tau2_reward") is not None]
        entry["tau2_reward"] = round(sum(t2) / len(t2), 4) if t2 else None
        entry["error_rate"] = round(sum(1 for r in group if r.get("error")) / len(group), 3)
        out.setdefault(domain, {})[variant] = entry
    return out


def main():
    all_data = {}
    for model, path in RUNS.items():
        with open(path, encoding="utf-8") as f:
            all_data[model] = json.load(f)

    means = {m: compute_means(rows) for m, rows in all_data.items()}

    stats = {
        "run_dirs": {m: str(p.parent) for m, p in RUNS.items()},
        "models": list(all_data.keys()),
        "total_rows": {m: len(r) for m, r in all_data.items()},
        "means": means,
    }

    reports = ROOT / "outputs/reports"
    reports.mkdir(parents=True, exist_ok=True)

    (reports / "grok_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print("Written: grok_stats.json")

    # --- Markdown ---
    lines = ["# Grok SAFE Benchmark Results\n"]
    lines.append("Models evaluated: **grok-3** and **grok-3-mini** (xAI API)")
    lines.append(f"- grok-3: {stats['total_rows']['grok-3']} evaluations")
    lines.append(f"- grok-3-mini: {stats['total_rows']['grok-3-mini']} evaluations\n")

    for model in ["grok-3", "grok-3-mini"]:
        lines.append(f"## {model}\n")
        lines.append("| domain | variant | n | S | A | F | E | safe_overall | tau2 | errors |")
        lines.append("|--------|---------|---|---|---|---|---|-------------|------|--------|")
        for domain in DOMAINS:
            for variant in VARIANTS:
                e = means[model].get(domain, {}).get(variant)
                if e:
                    t2 = f"{e['tau2_reward']:.3f}" if e["tau2_reward"] is not None else "n/a"
                    lines.append(
                        f"| {domain} | {variant} | {e['n']} "
                        f"| {e['scope']:.2f} | {e['anchored_decisions']:.2f} "
                        f"| {e['flow_integrity']:.2f} | {e['escalation']:.2f} "
                        f"| {e['safe_overall']:.2f} | {t2} | {e['error_rate']:.0%} |"
                    )
        lines.append("")

    lines.append(
        "> **Note:** `binding-only` scores reflect 100% API errors (xAI credit exhaustion)."
        " That variant ran last in both sweeps; all 120 binding-only tasks per model returned"
        " HTTP 403 and produced no agent turns. Disregard binding-only Grok results.\n"
    )
    lines.append("## Cross-model comparison (safe-aware variant)\n")
    lines.append("| domain | metric | grok-3 | grok-3-mini |")
    lines.append("|--------|--------|--------|-------------|")
    for domain in DOMAINS:
        for dim, label in [("scope","S"), ("anchored_decisions","A"),
                           ("flow_integrity","F"), ("escalation","E"), ("safe_overall","overall")]:
            g3  = means["grok-3"].get(domain, {}).get("safe-aware", {}).get(dim)
            gm  = means["grok-3-mini"].get(domain, {}).get("safe-aware", {}).get(dim)
            g3s  = f"{g3:.3f}"  if g3  is not None else "n/a"
            gms  = f"{gm:.3f}"  if gm  is not None else "n/a"
            lines.append(f"| {domain} | {label} | {g3s} | {gms} |")
    lines.append("")

    (reports / "grok_stats.md").write_text("\n".join(lines), encoding="utf-8")
    print("Written: grok_stats.md")


if __name__ == "__main__":
    main()
