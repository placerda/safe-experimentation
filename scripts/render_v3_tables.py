"""Render v3 results tables (markdown) from outputs/reports/v3_stats.json.

Run AFTER `analyze_v3.py --auto` has produced v3_stats.json.

Usage:
    python scripts/render_v3_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATS = ROOT / "outputs" / "reports" / "v3_stats.json"
OUT = ROOT / "outputs" / "reports" / "v3_tables.md"


def fmt_table(rows: list[dict], cols: list[str] | None = None) -> str:
    if not rows:
        return "_(no rows)_"
    cols = cols or list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def main() -> None:
    if not STATS.exists():
        raise SystemExit(f"missing {STATS}; run scripts/analyze_v3.py --auto first")
    s = json.loads(STATS.read_text(encoding="utf-8"))
    sections: list[str] = []
    sections.append("### Table 1 — H1 (safe-aware vs baseline) and H3 (ablation contrasts) on CVFR\n")
    sections.append(fmt_table(s["mcnemar_cvfr"]))
    sections.append("\n### Table 2 — H2 TOST non-inferiority on tau2_reward (Δ_NI = 0.05)\n")
    sections.append(fmt_table(s["tost_reward"]))
    sections.append("\n### Table 3 — Reliability: safe_pass^k\n")
    sections.append(fmt_table(s["pass_at_k"]))
    sections.append("\n### Inputs\n")
    sections.append("Runs aggregated: " + ", ".join(s.get("input_runs", [])))
    OUT.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
