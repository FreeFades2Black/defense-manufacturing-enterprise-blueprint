<!--
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        01-cmmc-enclave-iac/README.md
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.1.1, 3.3.1, 3.4.1, 3.4.2, 3.5.3, 3.13.1, 3.13.8, 3.13.11
ITIL 4 / PMI:    ITIL 4 Infrastructure & Platform Mgmt, Service Config Mgmt |
                 PMI Risk Mitigation & Technical Baseline Control
================================================================================
-->

# Module 01: CMMC Level 2 Hybrid Enclave Baseline (`01-cmmc-enclave-iac`)

This module defines the vendor-neutral Infrastructure-as-Code (Terraform) and Windows Server / Active Directory PowerShell engineering baseline for the regulated manufacturing enclave (`enclave-cui-prod` at `site-mfg-01`).

## Sanitized Network & Domain Topology (RFC-5737 Compliant)

| Boundary Zone | Identifier | Subnet CIDR (RFC-5737) | Security & Operational Purpose |
| :--- | :--- | :--- | :--- |
| **CUI Regulated Enclave** | `enclave-cui-prod` | `192.0.2.0/24` | Hosts IFS Cloud ERP middleware, Aras Innovator PLM vaults, and CUI file/database tiers. |
| **Site Manufacturing DMZ** | `site-mfg-01` | `198.51.100.0/24` | Hosts MES/OT data collectors, ServiceNow MID Server (`mid-mfg-01.example-mfg.local`), and badge terminals. |
| **Corporate IT Transit** | `org-enterprise-it` | `203.0.113.0/24` | Enterprise identity transit, SIEM forwarders, and PAM jump hosts (`example-mfg.local`). |

## Artifact-to-Control Traceability

| File | NIST SP 800-171 Rev 2 Controls | ITIL 4 / PMI Governance Outcome |
| :--- | :--- | :--- |
| [`main.tf`](main.tf) | `3.3.1`, `3.3.2`, `3.4.1` | Centralized immutable audit logging (365-day retention) & mandatory FinOps/CMDB tagging. |
| [`variables.tf`](variables.tf) | `3.4.1`, `3.4.2` | Standardized baseline configuration parameters with RFC-5737 CIDR validation. |
| [`network_enclave.tf`](network_enclave.tf) | `3.1.20`, `3.13.1`, `3.13.6` | Default-deny micro-segmentation between `enclave-cui-prod`, `site-mfg-01`, and `org-enterprise-it`. |
| [`identity_conditional_access.tf`](identity_conditional_access.tf) | `3.1.1`, `3.1.5`, `3.5.3` | Phishing-resistant MFA (FIDO2/PIV) and compliant device enforcement for GCC High enclave access. |
| [`keyvault_tls.tf`](keyvault_tls.tf) | `3.13.8`, `3.13.10`, `3.13.11` | FIPS 140-2/3 HSM-backed cryptographic key storage and automated TLS certificate rotation. |
| [`powershell/Invoke-EnclaveReadOnlyDiscovery.ps1`](powershell/Invoke-EnclaveReadOnlyDiscovery.ps1) | `3.1.1`, `3.4.1`, `3.11.2` | Week-1 non-destructive AD/Entra identity hygiene and Windows Server capacity baseline discovery. |
| [`powershell/EnclaveServerBaselineDSC.ps1`](powershell/EnclaveServerBaselineDSC.ps1) | `3.4.2`, `3.13.8`, `3.13.11` | Automated Windows Server hardening (FIPS mode, TLS 1.2/1.3, SMBv3 signing, audit policy). |
| [`powershell/Test-TlsCertificateLifecycle.ps1`](powershell/Test-TlsCertificateLifecycle.ps1) | `3.13.8`, `3.12.3` | Proactive TLS certificate expiration and cipher strength verification across ERP/PLM endpoints. |
