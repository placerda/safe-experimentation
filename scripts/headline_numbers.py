"""Compute headline aggregates for the paper."""
import json
from collections import defaultdict
from pathlib import Path
import sys

run_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/runs/20260425_112848")
r = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))

agg = defaultdict(lambda: defaultdict(list))
for e in r:
    key = (e["domain"], e["agent_variant"])
    for d in ["safe_overall", "scope", "anchored_decisions", "flow_integrity", "escalation"]:
        agg[key][d].append(e[d])
    agg[key]["completed"].append(int(e["task_completed"]))

print(f"{'domain/variant':<26}{'n':>4}{'safe':>7}{'scope':>7}{'anch':>7}{'flow':>7}{'esc':>7}{'compl':>7}")
print("-" * 72)
for k in sorted(agg):
    v = agg[k]
    n = len(v["safe_overall"])
    row = [sum(v[d]) / n for d in ["safe_overall", "scope", "anchored_decisions", "flow_integrity", "escalation", "completed"]]
    print(f"{k[0]+'/'+k[1]:<26}{n:>4}" + "".join(f"{x:>7.3f}" for x in row))

print()
for variant in ["baseline", "safe-aware"]:
    vals = [e["safe_overall"] for e in r if e["agent_variant"] == variant]
    completed = [int(e["task_completed"]) for e in r if e["agent_variant"] == variant]
    print(f"OVERALL {variant:<12}: safe_mean={sum(vals)/len(vals):.3f}  completion={sum(completed)/len(completed):.2f}  (n={len(vals)})")
