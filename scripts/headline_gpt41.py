"""Compute headline numbers for the gpt-4.1 re-run."""
import json
from collections import defaultdict

data = json.load(open("outputs/runs/20260426_140931/results.json", encoding="utf-8"))
by_v = defaultdict(list)
for r in data:
    by_v[r["agent_variant"]].append(r)

print("=== OVERALL ===")
for v, rs in by_v.items():
    n = len(rs)
    safe = sum(r["safe_overall"] for r in rs) / n
    comp = sum(r["task_completed"] for r in rs) / n
    t3vals = [r["tau2_reward"] for r in rs if r["tau2_reward"] is not None]
    t3 = sum(t3vals) / len(t3vals) if t3vals else None
    t3str = f"{t3:.3f}" if t3 is not None else "n/a"
    print(f"{v}: n={n} safe={safe:.3f} task_completed={comp:.3f} t3_reward(n={len(t3vals)})={t3str}")

print("\n=== BY DOMAIN ===")
for v in by_v:
    for d in ["airline", "retail"]:
        rs = [r for r in by_v[v] if r["domain"] == d]
        n = len(rs)
        safe = sum(r["safe_overall"] for r in rs) / n
        comp = sum(r["task_completed"] for r in rs) / n
        t3vals = [r["tau2_reward"] for r in rs if r["tau2_reward"] is not None]
        t3 = sum(t3vals) / len(t3vals) if t3vals else None
        t3str = f"{t3:.3f}" if t3 is not None else "n/a"
        print(f"{v}/{d}: n={n} safe={safe:.3f} comp={comp:.3f} t3(n={len(t3vals)})={t3str}")

print("\n=== PER-DIMENSION ===")
for v, rs in by_v.items():
    for k in ["scope", "anchored_decisions", "flow_integrity", "escalation"]:
        avg = sum(r[k] for r in rs) / len(rs)
        print(f"{v}: {k}={avg:.3f}")
