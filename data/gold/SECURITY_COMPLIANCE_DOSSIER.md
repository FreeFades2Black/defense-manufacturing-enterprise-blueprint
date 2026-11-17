# Automated CMMC Level 2 & NIST SP 800-171 Security Compliance Dossier

- **Dossier ID**: `DOSSIER-CMMC-L2-2026-Q4`
- **Generated (UTC)**: `2026-11-17T21:50:56Z`
- **Enclave Scope**: `enclave-cui-prod` | `site-mfg-01` | `example-mfg.local`
- **CI/CD Policy Gate Status**: **PASSED** (6/6 Control Groups Verified — 100.0%)

## Automated Control Verification Matrix

| NIST SP 800-171 Control | Control Family | Technical Requirement | Artifact Verified | ITIL 4 / PMI Outcome | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `3.1.1 / 3.5.3` | Access Control & Identification/Authentication | Phishing-resistant MFA (FIDO2/PIV) & compliant device Conditional Access for enclave-cui-prod | `01-cmmc-enclave-iac/identity_conditional_access.tf` | ITIL 4 Access Mgmt / Zero Unauthorized CUI Sessions | **PASS** |
| `3.3.1 / 3.3.2` | Audit and Accountability | Immutable SIEM audit workspace with >=365-day log retention and disabled public ingestion | `01-cmmc-enclave-iac/main.tf` | ITIL 4 Information Security Mgmt / C3PAO Audit Evidence | **PASS** |
| `3.4.1 / 3.4.2` | Configuration Management | Mandatory CMDB/FinOps tagging and Windows Server DSC hardening (SMBv1 disabled, SMBv3 signed) | `01-cmmc-enclave-iac/powershell/EnclaveServerBaselineDSC.ps1` | ITIL 4 Service Configuration Mgmt / Drift Prevention | **PASS** |
| `3.8.9` | Media Protection & Recovery | Locked immutable GeoRedundant Recovery Services Vault with public network access disabled | `01-cmmc-enclave-iac/main.tf` | ITIL 4 Service Continuity Mgmt / ERP & PLM Cutover Rollback Safety | **PASS** |
| `3.13.1 / 3.13.6` | System and Communications Protection | Default-deny NSG micro-segmentation across RFC-5737 zones (192.0.2.0/24, 198.51.100.0/24) | `01-cmmc-enclave-iac/network_enclave.tf` | ITIL 4 Infrastructure & Platform Mgmt / Enclave Boundary Isolation | **PASS** |
| `3.13.8 / 3.13.11` | Cryptographic Protection | FIPS 140-2/3 HSM-backed Premium Key Vault, 4096-bit RSA-HSM TLS certs, and Windows FIPS policy | `01-cmmc-enclave-iac/keyvault_tls.tf` | PMI Technical Risk Mitigation / Zero Expired Cert Cutover Outages | **PASS** |
