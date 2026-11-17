<!--
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        docs/SHARED_RESPONSIBILITY_MATRIX.md
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.1.1 (Access Control), 3.4.2 (Security Configuration),
                 3.12.1 (Security Assessment), 3.13.1 (Boundary Protection)
ITIL 4 / PMI:    ITIL 4 Information Security Management & Service Level Mgmt |
                 PMI Governance RACI & Regulatory Compliance Alignment
================================================================================
-->

# Shared Responsibility Matrix: Corporate IT vs. Regulated Manufacturing Enclave

This matrix establishes clear organizational accountability across **Corporate IT** (`org-enterprise-it`), **Regulated CUI Enclave Operations** (`enclave-cui-prod`), **Site Manufacturing IT/OT** (`site-mfg-01`), and the **Technical Program Manager / Senior Systems Engineer (TPM/Sr. SE)**.

## Legend
- **R**: Responsible (Executes engineering/operational task)
- **A**: Accountable (Approves boundary/governance artifact)
- **C**: Consulted (Provides architectural/security input)
- **I**: Informed (Receives automated telemetry/dossiers)

| Control Family | NIST SP 800-171 Control | Technical Capability | `org-enterprise-it` (Corporate IT) | `enclave-cui-prod` (Enclave ISSM / SecOps) | `site-mfg-01` (Site IT / OT) | Unified TPM / Sr. SE | Verification Artifact in Repo |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Access Control (AC)** | `3.1.1` / `3.1.5` | Entra ID GCC High Conditional Access & Least Privilege RBAC | C | A | I | **R** | `01-cmmc-enclave-iac/identity_conditional_access.tf` |
| **Access Control (AC)** | `3.1.20` | External Connection & Boundary Enforcement (`192.0.2.0/24`) | R | A | C | **R** | `01-cmmc-enclave-iac/network_enclave.tf` |
| **Audit & Accountability (AU)** | `3.3.1` / `3.3.2` | Centralized SIEM/Log Analytics & User Action Traceability | C | A | I | **R** | `01-cmmc-enclave-iac/main.tf` |
| **Configuration Mgmt (CM)** | `3.4.1` / `3.4.2` | Windows Server Hardening Baseline & CMDB CI Accuracy | I | A | C | **R** | `01-cmmc-enclave-iac/powershell/EnclaveServerBaselineDSC.ps1` |
| **Identification & Auth (IA)** | `3.5.3` | Phishing-Resistant MFA (FIDO2 / PIV) for Enclave Access | C | A | I | **R** | `03-policy-as-code-governance/policies/cmmc_enclave_guardrails.rego` |
| **Maintenance (MA)** | `3.7.1` / `3.7.2` | Controlled Maintenance & OS Patch Compliance Windows | I | C | R | **A** | `01-cmmc-enclave-iac/powershell/Invoke-EnclaveReadOnlyDiscovery.ps1` |
| **Risk Assessment (RA)** | `3.11.1` / `3.11.2` | Continuous Vulnerability & Queue Bottleneck Telemetry | I | A | C | **R** | `02-itsm-medallion-telemetry/pipeline.py` |
| **Security Assessment (CA)** | `3.12.1` / `3.12.4` | Automated SSP / POA&M Security Dossier Generation | I | A | I | **R** | `03-policy-as-code-governance/generate_security_dossier.py` |
| **System & Comms Protection (SC)** | `3.13.1` / `3.13.8` / `3.13.11` | FIPS 140-2/3 Validated TLS 1.2/1.3 & Micro-Segmentation | C | A | C | **R** | `01-cmmc-enclave-iac/powershell/Test-TlsCertificateLifecycle.ps1` |
| **Program & FinOps Governance** | `PMI-EVM` / `ITIL-4` | ERP/PLM Cutover Readiness, CPI/SPI & Budget Guardrails | I | C | C | **R/A** | `04-program-command-gateway/app.py` |
