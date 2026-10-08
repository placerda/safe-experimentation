# Tool-call error audit

Harness-bug signature: `has no attribute 'get_response'`.
A run is **INVALID** when more than 5% of its tool calls hit the harness bug.

| Source | Run | Traces | Tool calls | Harness-bug rate | Other error/block rate | Status |
|---|---|---:|---:|---:|---:|---|
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_145304` | 20 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_150152` | 16 | 92 | 0.0% | 3.3% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_152614` | 9 | 53 | 0.0% | 3.8% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_153927` | 20 | 120 | 0.0% | 1.7% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_221148` | 60 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260424_221902` | 60 | 398 | 0.0% | 3.0% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260425_105056` | 8 | 48 | 0.0% | 8.3% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260425_112848` | 60 | 417 | 0.0% | 3.4% | ok |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_140718` | 1 | 3 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_140840` | 2 | 10 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_140931` | 60 | 188 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_170919__smoke-gpt41` | 4 | 12 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_171105__smoke-gpt5mini` | 4 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_171210__smoke-gpt5mini2` | 4 | 29 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_172556__gpt-4.1` | 200 | 658 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260426_172704__gpt-5-mini` | 200 | 836 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260427_184832__smoke-telecom` | 1 | 3 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260427_200216__v3-extra-seeds` | 400 | 1314 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260428_095513__v3-ablation` | 600 | 1769 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260428_163342__v3-telecom` | 80 | 9 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_111436__smoke3` | 1 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_111631__smoke4` | 1 | 3 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_111729__v3-retry` | 9 | 35 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_112249__v3-retry` | 1 | 3 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_112357__v3-retry` | 24 | 77 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_114148__v3-retry` | 3 | 12 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_114547__v3-retry` | 1 | 2 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_114640__v3-retry` | 21 | 44 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_120046__v3-retry` | 34 | 72 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_122823__v3-retry` | 0 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_122932__v3-retry` | 1 | 2 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_173923__smoke-v4-env` | 1 | 4 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_174631__smoke-v4-bind` | 2 | 7 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_174904__smoke-v4-rest` | 8 | 24 | 95.8% | 4.2% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_175838__smoke-v4-full` | 18 | 57 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_182730__smoke-v4-esc-tuned` | 6 | 17 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_183342__dry-v4` | 30 | 119 | 99.2% | 0.8% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260429_185933__auth-test` | 0 | 0 | 0.0% | 0.0% | no tool calls |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260513_202953__smoke-newenv` | 1 | 4 | 100.0% | 0.0% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260513_203156__v4-seed1` | 600 | 2532 | 97.5% | 2.5% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260514_011035__v4-seed2` | 600 | 2437 | 97.7% | 2.3% | INVALID |
| `C:\Users\paulolacerda\workspace\safe-experimentation\outputs\runs` | `20260514_135049__v4-seed3` | 600 | 2470 | 97.6% | 2.4% | INVALID |
| `outputs\runs` | `20260425_105056` | 8 | 48 | 0.0% | 8.3% | ok |
| `outputs\runs` | `20260425_112848` | 60 | 417 | 0.0% | 3.4% | ok |
| `outputs\runs` | `20260426_140840` | 2 | 10 | 100.0% | 0.0% | INVALID |
| `outputs\runs` | `20260426_140931` | 60 | 188 | 100.0% | 0.0% | INVALID |
| `outputs\runs` | `20260426_172556__gpt-4.1` | 200 | 658 | 100.0% | 0.0% | INVALID |
| `outputs\runs` | `20260426_172704__gpt-5-mini` | 200 | 836 | 100.0% | 0.0% | INVALID |
| `outputs\runs` | `20261005_151158__pilot-gpt-5.4` | 20 | 45 | 97.8% | 2.2% | INVALID |
| `outputs\runs` | `20261005_151758__full-gpt-5.4` | 720 | 1479 | 94.5% | 5.5% | INVALID |
