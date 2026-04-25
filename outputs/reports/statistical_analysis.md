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
| scope | sign_test † | 3 | -0.0333 | [-0.133, +0.067] | 1.0000 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 4 | +0.0000 | [-0.030, +0.030] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 5 | -0.0022 | [-0.039, +0.039] | 1.0000 | 1.0000 | — |  |
| escalation | sign_test † | 4 | +0.0667 | [-0.033, +0.200] | 0.6250 | 1.0000 | — |  |
| **safe_overall** (P) | wilcoxon | 11 | +0.0078 | [-0.038, +0.050] | 0.5612 | — | 0.197 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used

## Airline Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 1 | +0.0667 | [+0.000, +0.200] | 1.0000 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 2 | +0.0000 | [-0.050, +0.050] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 2 | -0.0033 | [-0.050, +0.040] | 1.0000 | 1.0000 | — |  |
| escalation | sign_test † | 3 | +0.2000 | [+0.000, +0.400] | 0.2500 | 1.0000 | — |  |
| **safe_overall** (P) | sign_test † | 5 | +0.0658 | [+0.015, +0.117] | 0.3750 | — | — |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used
- **safe_overall**: Too few nonzero pairs for Wilcoxon; sign test used

## Retail Domain

| Dimension | Test | n* | Mean Δ | 95% CI | p | p (Holm) | r | Sig |
|-----------|------|----|--------|--------|---|----------|---|-----|
| scope | sign_test † | 2 | -0.1333 | [-0.333, +0.000] | 0.5000 | 1.0000 | — |  |
| anchored_decisions | sign_test † | 2 | +0.0000 | [-0.040, +0.040] | 1.0000 | 1.0000 | — |  |
| flow_integrity | sign_test † | 3 | -0.0011 | [-0.061, +0.069] | 1.0000 | 1.0000 | — |  |
| escalation | sign_test † | 1 | -0.0667 | [-0.200, +0.000] | 1.0000 | 1.0000 | — |  |
| **safe_overall** (P) | wilcoxon | 6 | -0.0503 | [-0.129, +0.006] | 0.2476 | — | -0.524 |  |

*n\* = nonzero pairs (ties excluded)*

**Notes:**
- **scope**: Too few nonzero pairs for Wilcoxon; sign test used
- **anchored_decisions**: Too few nonzero pairs for Wilcoxon; sign test used
- **flow_integrity**: Too few nonzero pairs for Wilcoxon; sign test used
- **escalation**: Too few nonzero pairs for Wilcoxon; sign test used

## Key Findings

1. **Primary endpoint (safe_overall)**: Safe-aware agent scores higher by 0.008 on average (95% CI: [-0.038, +0.050])
   - Wilcoxon p=0.5612 (not statistically significant at α=0.05)
2. **Airline**: improvement of 0.066 in overall SAFE score
   - Largest effect in **escalation**: Δ=+0.200, sign test (ties too frequent for effect size)
3. **Retail**: regression of 0.050 in overall SAFE score
   - Largest effect in **scope**: Δ=-0.133, sign test (ties too frequent for effect size)

## Limitations

- Small sample size (n=15 per domain) limits statistical power
- Binary dimensions (scope, escalation) produce many ties, reducing effective sample for Wilcoxon
- Results should be interpreted as exploratory evidence, not definitive proof of effect
