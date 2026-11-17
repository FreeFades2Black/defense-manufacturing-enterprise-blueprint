# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        03-policy-as-code-governance/policies/finops_budget_gate.rego
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.4.3 (Track, Review, Approve or Disapprove System Changes)
# ITIL 4 / PMI:    ITIL 4 Service Financial Management |
#                  PMI Earned Value Management (CPI >= 1.00 Budget Guardrail)
# ==============================================================================

package defense.mfg.finops

import future.keywords.contains
import future.keywords.if

max_monthly_budget_usd := 18500.0
max_pr_delta_pct := 8.0

deny contains msg if {
    total_monthly := to_number(input.totalMonthlyCost)
    total_monthly > max_monthly_budget_usd
    msg := sprintf(
        "[FinOps-CPI-Gate] Projected monthly cost ($%.2f) exceeds approved enclave budget ($%.2f).",
        [total_monthly, max_monthly_budget_usd]
    )
}

deny contains msg if {
    diff_pct := to_number(input.diffTotalMonthlyCostPct)
    diff_pct > max_pr_delta_pct
    msg := sprintf(
        "[FinOps-CAB-Gate] PR monthly cost increase (%.2f%%) exceeds %.1f%% threshold; PMO/CAB approval required.",
        [diff_pct, max_pr_delta_pct]
    )
}
