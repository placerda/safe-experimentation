"""Render v4 paper-ready tables from outputs/reports/v4_stats.json.

Produces outputs/reports/v4_tables.md with three tables:

  1. Per-dimension means by (variant, domain) — flattened, paper-friendly.
  2. H1' headline table — Δ + Holm-corrected p, with stars.
  3. Guardrail event firing-rate per variant.

Usage:
    python scripts/render_v4_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATS = ROOT / "outputs" / "reports" / "v4_stats.json"
OUT = ROOT / "outputs" / "reports" / "v4_tables.md"


def stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def main() -> None:
    if not STATS.exists():
        raise SystemExit(f"Missing {STATS}; run analyze_v4.py first.")
    s = json.loads(STATS.read_text(encoding="utf-8"))
    means = s.get("means", {})
    h1 = s.get("h1_per_dimension", [])
    h2 = s.get("h2_non_inferiority", [])
    h3 = s.get("h3_composability", [])
    events = s.get("guardrail_events", {})

    lines: list[str] = []
    lines.append("# v4 paper-ready tables\n")

    # Table 1 — per-dimension means (paper format).
    lines.append("## Table 1. Per-dimension SAFE scores by variant and domain\n")
    lines.append("Continuous scores in [0,1]. CVFR is the rate of fully-clean cells. Reward = τ³-bench official reward.\n")
    lines.append("| Variant | Domain | n | Scope | Anchored | Flow | Escalation | CVFR | Reward |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    variant_order = ["baseline", "binding", "evidence", "flow", "escalation", "all-guardrails"]
    domain_order = ["airline", "retail"]
    for v in variant_order:
        for d in domain_order:
            m = means.get(v, {}).get(d)
            if not m:
                continue
            r = "—" if m.get("tau2_reward") is None else f"{m['tau2_reward']:.3f}"
            lines.append(
                f"| {v} | {d} | {m['n']} | {m['scope']:.3f} | "
                f"{m['anchored_decisions']:.3f} | {m['flow_integrity']:.3f} | "
                f"{m['escalation']:.3f} | {m['cvfr_pass_rate']:.3f} | {r} |"
            )
    lines.append("")

    # Table 2 — H1' headline.
    lines.append("## Table 2. H1' — per-dimension lift vs baseline (paired bootstrap)\n")
    lines.append("Δ = mean(target variant) − mean(baseline). 95% CI from paired bootstrap (10 000 resamples). p_holm = Holm-Bonferroni adjusted within the 4-contrast H1' family. Stars: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001 on Holm-adjusted p.\n")
    lines.append("| Dim | Domain | Target | n | Δ | 95% CI | p (raw) | p (Holm) |")
    lines.append("|---|---|---|---:|---:|---|---:|---:|")
    for r in h1:
        lines.append(
            f"| {r['dimension']} | {r['domain']} | {r['target_variant']} | {r['n_pairs']} "
            f"| {r['delta_mean']:+.3f} | [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}] "
            f"| {r['p_value']:.3f} | {r['p_holm']:.3f}{stars(r['p_holm'])} |"
        )
    lines.append("")

    # Table 3 — H2' utility.
    lines.append("## Table 3. H2' — utility non-inferiority (τ³ reward, Δ_NI = 0.05)\n")
    lines.append("Reject inferiority iff lower one-sided 90% bootstrap CI on (variant − baseline) > −0.05. Holm-adjusted within the 5-variant H2' family.\n")
    lines.append("| Variant | Domain | n | Δ reward | 90% lower | Non-inferior | p_holm |")
    lines.append("|---|---|---:|---:|---:|---|---:|")
    for r in h2:
        lines.append(
            f"| {r['variant']} | {r['domain']} | {r['n_pairs']} "
            f"| {r['delta_mean']:+.3f} | {r['ci90_low']:+.3f} "
            f"| {'**yes**' if r['reject_inferiority'] else 'no'} | {r['p_holm']:.3f} |"
        )
    lines.append("")

    # Table 4 — H3' composability.
    if h3:
        lines.append("## Table 4. H3' — composability of all-guardrails vs single-enforcer target\n")
        lines.append("Δ = mean(all-guardrails) − mean(single-enforcer target on its dimension). Negative = composing hurts.\n")
        lines.append("| Dim | Domain | n | Δ vs target | 95% CI | Interpretation |")
        lines.append("|---|---|---:|---:|---|---|")
        for r in h3:
            lines.append(
                f"| {r['dimension']} | {r['domain']} | {r['n_pairs']} "
                f"| {r['delta_mean_vs_target']:+.3f} | [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}] "
                f"| {r['interpretation']} |"
            )
        lines.append("")

    # Table 5 — event firing.
    lines.append("## Table 5. Guardrail event firing summary\n")
    lines.append("Counts of enforcer hook firings across all traces, per variant.\n")
    all_keys = set()
    for v_d in events.values():
        all_keys.update(v_d.keys())
    keys_sorted = sorted(all_keys)
    if keys_sorted:
        header = "| Variant | " + " | ".join(keys_sorted) + " |"
        sep = "|---|" + "|".join("---:" for _ in keys_sorted) + "|"
        lines.append(header)
        lines.append(sep)
        for v in variant_order:
            row = events.get(v)
            if not row:
                continue
            cells = [str(row.get(k, 0)) for k in keys_sorted]
            lines.append(f"| {v} | " + " | ".join(cells) + " |")
    else:
        lines.append("(No guardrail events recorded.)")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
