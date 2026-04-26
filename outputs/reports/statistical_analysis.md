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
| scope | wilcoxon | 20 | +0.0600 | [-0.030, +0.150] | 0.1797 | 1.0000 | 0.300 |  |
| anchored_decisions | sign_test † | 5 | -0.0068 | [-0.017, +0.001] | 0.3750 | 1.0000 | — |  |
| flow_integrity | wilcoxon | 18 | +0.0133 | [-0.006, +0.034] | 0.2841 | 1.0000 | 0.287 |  |
| escalation | sign_test † | 1 | +0.0100 | [+0.000, +0.030] | 1.0000 | 1.0000 | — |  |
| **safe_overall** (P) | wilcoxon | 38 | +0.0191 | [-0.004, +0.043] | 0.0969 | — | 0.308 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used

## Airline Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | wilcoxon | 7 | +0.1400 | [+0.060, +0.240] | 0.0082 | 0.0897 | 1.000 |  |
| anchored_decisions | sign_test † | 2 | -0.0060 | [-0.016, +0.000] | 0.5000 | 1.0000 | — |  |
| flow_integrity | wilcoxon | 16 | +0.0276 | [-0.010, +0.068] | 0.2218 | 1.0000 | 0.346 |  |
| escalation | none † | 0 | +0.0000 | [+0.000, +0.000] | n/a | — | — |  |
| **safe_overall** (P) | wilcoxon | 20 | +0.0404 | [+0.016, +0.070] | 0.0104 | — | 0.652 | ✱ |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: All pairs tied — no test possible

## Retail Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | wilcoxon | 13 | -0.0200 | [-0.160, +0.120] | 0.7815 | 1.0000 | -0.077 |  |
| anchored_decisions | sign_test † | 3 | -0.0075 | [-0.025, +0.005] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 2 | -0.0011 | [-0.010, +0.007] | 1.0000 | 1.0000 | — |  |
| escalation | sign_test † | 1 | +0.0200 | [+0.000, +0.060] | 1.0000 | — | — |  |
| **safe_overall** (P) | wilcoxon | 18 | -0.0022 | [-0.039, +0.035] | 0.6567 | — | 0.117 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used

## Key Findings

1. **Primary endpoint (safe_overall)**: Safe-aware agent scores higher by 0.019 on average (95% CI: [-0.004, +0.043])
   - Wilcoxon p=0.0969 (not statistically significant at α=0.05)
2. **Airline**: improvement of 0.040 in overall SAFE score
   - Largest effect in **scope**: Δ=+0.140, r=1.000
3. **Retail**: regression of 0.002 in overall SAFE score
   - Largest effect in **scope**: Δ=-0.020, r=-0.077

## Limitations

- Small sample size (n=15 per domain) limits statistical power
- Binary dimensions (scope, escalation) produce many ties, reducing effective sample for Wilcoxon
- Results should be interpreted as exploratory evidence, not definitive proof of effect
