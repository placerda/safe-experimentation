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
| scope | sign_test † | 4 | +0.1333 | [+0.033, +0.267] | 0.1250 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 5 | -0.0017 | [-0.043, +0.044] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 4 | -0.0050 | [-0.043, +0.028] | 1.0000 | 1.0000 | — |  |
| escalation | wilcoxon | 9 | +0.1000 | [-0.100, +0.300] | 0.3173 | 1.0000 | 0.333 |  |
| **safe_overall** (P) | wilcoxon | 18 | +0.0567 | [-0.006, +0.119] | 0.1817 | — | 0.357 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used

## Airline Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 2 | +0.1333 | [+0.000, +0.333] | 0.5000 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 3 | +0.0356 | [-0.022, +0.113] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 3 | +0.0167 | [-0.033, +0.067] | 1.0000 | 1.0000 | — |  |
| escalation | wilcoxon | 7 | +0.2000 | [-0.133, +0.533] | 0.2568 | 1.0000 | 0.429 |  |
| **safe_overall** (P) | wilcoxon | 11 | +0.0964 | [-0.008, +0.201] | 0.1291 | — | 0.515 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used

## Retail Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 2 | +0.1333 | [+0.000, +0.333] | 0.5000 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 2 | -0.0389 | [-0.100, +0.000] | 0.5000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 1 | -0.0267 | [-0.080, +0.000] | 1.0000 | 1.0000 | — |  |
| escalation | sign_test † | 2 | +0.0000 | [-0.200, +0.200] | 1.0000 | 1.0000 | — |  |
| **safe_overall** (P) | wilcoxon | 7 | +0.0169 | [-0.049, +0.088] | 0.6095 | — | 0.214 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used

## Key Findings

1. **Primary endpoint (safe_overall)**: Safe-aware agent scores higher by 0.057 on average (95% CI: [-0.006, +0.119])
   - Wilcoxon p=0.1817 (not statistically significant at α=0.05)
2. **Airline**: improvement of 0.096 in overall SAFE score
   - Largest effect in **escalation**: Δ=+0.200, r=0.429
3. **Retail**: improvement of 0.017 in overall SAFE score
   - Largest effect in **scope**: Δ=+0.133, sign test (ties too frequent for effect size)

## Limitations

- Small sample size (n=15 per domain) limits statistical power
- Binary dimensions (scope, escalation) produce many ties, reducing effective sample for Wilcoxon
- Results should be interpreted as exploratory evidence, not definitive proof of effect
