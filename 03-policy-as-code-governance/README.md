<!--
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        03-policy-as-code-governance/README.md
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.3.1, 3.4.2, 3.4.3, 3.5.3, 3.12.1, 3.12.4, 3.13.1, 3.13.11
ITIL 4 / PMI:    ITIL 4 Change Enablement & Financial Mgmt |
                 PMI Cost Management (CPI Guardrail) & Continuous Audit Readiness
================================================================================
-->

# Module 03: Continuous Compliance & FinOps Gate (`03-policy-as-code-governance`)

This module embeds **NIST SP 800-171 Rev 2 / CMMC Level 2** security controls and **FinOps budget guardrails** directly into CI/CD pull request gates—eliminating manual post-deployment compliance audits and unapproved cloud cost drift.

## Key Capabilities

1. **Zero-Trust OPA/Rego Policy Checks (`policies/cmmc_enclave_guardrails.rego`)**:
   - Blocks any Terraform plan that:
     - Sets SIEM audit log retention below **365 days** (`NIST 3.3.1`).
     - Permits inbound `0.0.0.0/0` or `*` traffic into the CUI enclave subnet `192.0.2.0/24` (`NIST 3.13.1` / `3.13.6`).
     - Uses a non-HSM (`standard`) Key Vault SKU instead of FIPS 140-2/3 `premium` HSM backing (`NIST 3.13.11`).
     - Omits mandatory CMDB/FinOps resource tags (`Organization`, `EnclaveBoundary`, `ManufacturingSite`, `ComplianceStandard`, `CostCenter`).
2. **FinOps Infracost Gate (`policies/finops_budget_gate.rego` & `evaluate_finops_gate.py`)**:
   - Enforces the approved **$18,500/month** enclave infrastructure ceiling and flags any PR increasing monthly spend by **>8.0%** for PMO/CAB review.
3. **Automated Security Dossier Generation (`generate_security_dossier.py`)**:
   - Produces a timestamped Markdown (`data/gold/SECURITY_COMPLIANCE_DOSSIER.md`) and JSON (`data/gold/security_compliance_dossier.json`) audit artifact ready for Enclave ISSM and C3PAO assessor review.
