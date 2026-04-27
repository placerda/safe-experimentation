import re, pathlib, collections, statistics as st
log = pathlib.Path('outputs/run_gpt-5-mini.log').read_text(encoding='utf-8', errors='ignore')
pat = re.compile(
    r'\[(\d+)/200\]\s+Running\s+(baseline|safe-aware)\s+on\s+(\w+)_(\d+).*?'
    r'SAFE overall:\s+([\d.]+)\s+\(S:([\d.]+)\s+A:([\d.]+)\s+F:([\d.]+)\s+E:([\d.]+)\)\s+t3:(\S+)',
    re.DOTALL,
)
recs = []
for m in pat.finditer(log):
    n, var, dom, tid, sc, s, a, f, e, t3 = m.groups()
    t3v = None if t3 == 'n/a' else float(t3)
    recs.append(dict(variant=var, domain=dom, task=f'{dom}_{tid}',
                     safe=float(sc), scope=float(s), anchored=float(a),
                     flow=float(f), escalation=float(e), tau2=t3v))
print(f'Parsed {len(recs)} completed evals')
groups = collections.defaultdict(list)
for r in recs:
    groups[(r['variant'], r['domain'])].append(r)
for k, v in sorted(groups.items()):
    safes = [r['safe'] for r in v]
    scopes = [r['scope'] for r in v]
    flows = [r['flow'] for r in v]
    escs = [r['escalation'] for r in v]
    t3s = [r['tau2'] for r in v if r['tau2'] is not None]
    t3mean = st.mean(t3s) if t3s else float('nan')
    print(f'  {k[0]:11s} {k[1]:8s} n={len(v):3d}  safe={st.mean(safes):.3f}  scope={st.mean(scopes):.3f}  flow={st.mean(flows):.3f}  esc={st.mean(escs):.3f}  tau2={t3mean:.3f} (n_t2={len(t3s)})')
done_b = {r['task'] for r in recs if r['variant'] == 'baseline'}
done_s = {r['task'] for r in recs if r['variant'] == 'safe-aware'}
print(f'baseline done: {len(done_b)}, safe-aware done: {len(done_s)}, paired: {len(done_b & done_s)}')
