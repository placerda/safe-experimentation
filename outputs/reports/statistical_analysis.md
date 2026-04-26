# Statistical Analysis Report

## Methodology

- **Primary endpoint**: `safe_overall` (confirmatory, α=0.05)
- **Exploratory endpoints**: per-dimension scores (Holm-Bonferroni corrected)
- **Paired test**: Wilcoxon signed-rank (≥6 nonzero pairs) or sign test (fallback)
- **Effect size**: rank-biserial correlation (r) for Wilcoxon results
- **Confidence intervals**: bootstrap (10000 resamples), 95% level
- **Combined CI**: stratified bootstrap preserving domain balance (15/15)
- **Zero differences**: excluded from Wilcoxon (Pratt's method: `zero_method='wilcox'`)

## Interpretation Guide

- **mean_diff > 0**: safe-aware agent scores higher (improvement)
- **mean_diff < 0**: baseline agent scores higher
- **r ∈ [-1, 1]**: rank-biserial effect size; |r| > 0.5 is large
- **(P)**: primary endpoint (uncorrected α); others use Holm correction
- **\***: statistically significant at α=0.05

## Combined (All Domains)

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | wilcoxon | 7 | +0.1667 | [+0.000, +0.333] | 0.0588 | 0.4703 | 0.714 |  |
| anchored_decisions | sign_test † | 2 | -0.0056 | [-0.033, +0.017] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 4 | -0.0028 | [-0.033, +0.028] | 1.0000 | 1.0000 | — |  |
| escalation | none † | 0 | +0.0000 | [+0.000, +0.000] | n/a | — | — |  |
| **safe_overall** (P) | wilcoxon | 11 | +0.0396 | [+0.000, +0.083] | 0.0894 | — | 0.576 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: All pairs tied — no test possible

## Airline Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 3 | +0.2000 | [+0.000, +0.400] | 0.2500 | 0.7500 | — |  |
| anchored_decisions | none † | 0 | +0.0000 | [+0.000, +0.000] | n/a | — | — |  |
| flow_integrity | sign_test † | 2 | +0.0000 | [-0.050, +0.050] | 1.0000 | 1.0000 | — |  |
| escalation | none † | 0 | +0.0000 | [+0.000, +0.000] | n/a | — | — |  |
| **safe_overall** (P) | sign_test † | 4 | +0.0500 | [+0.008, +0.100] | 0.1250 | — | — |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: All pairs tied — no test possible
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: All pairs tied — no test possible
- **safe_overall**: Too few nonzero pairs for Wilcoxon; sign test used

## Retail Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 4 | +0.1333 | [-0.133, +0.400] | 0.6250 | — | — |  |
| anchored_decisions | sign_test † | 2 | -0.0111 | [-0.067, +0.033] | 1.0000 | — | — |  |
| flow_integrity | sign_test † | 2 | -0.0056 | [-0.050, +0.033] | 1.0000 | — | — |  |
| escalation | none † | 0 | +0.0000 | [+0.000, +0.000] | n/a | — | — |  |
| **safe_overall** (P) | wilcoxon | 7 | +0.0292 | [-0.036, +0.100] | 0.4461 | — | 0.321 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: All pairs tied — no test possible

## Key Findings

1. **Primary endpoint (safe_overall)**: Safe-aware agent scores higher by 0.040 on average (95% CI: [+0.000, +0.083])
   - Wilcoxon p=0.0894 (not statistically significant at α=0.05)
2. **Airline**: improvement of 0.050 in overall SAFE score
   - Largest effect in **scope**: Δ=+0.200, sign test (ties too frequent for effect size)
3. **Retail**: improvement of 0.029 in overall SAFE score
   - Largest effect in **scope**: Δ=+0.133, sign test (ties too frequent for effect size)

## Limitations

- Small sample size (n=15 per domain) limits statistical power
- Binary dimensions (scope, escalation) produce many ties, reducing effective sample for Wilcoxon
- Results should be interpreted as exploratory evidence, not definitive proof of effect
