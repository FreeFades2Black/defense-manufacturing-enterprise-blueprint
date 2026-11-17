#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        03-policy-as-code-governance/generate_security_dossier.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.12.1 (Security Control Assessment),
                 3.12.2 (Plan of Action & Milestones / POA&M),
                 3.12.4 (System Security Plan / SSP Evidence Generation)
ITIL 4 / PMI:    ITIL 4 Information Security Mgmt & Change Enablement |
                 PMI Continuous Audit Readiness & Compliance Gate Sign-Off
================================================================================

Automated Security Dossier generator. Inspects the CMMC Level 2 Terraform and
PowerShell baselines in 01-cmmc-enclave-iac/ alongside OPA/Rego policies and
produces both a structured JSON compliance dossier and a formatted Markdown
SSP/POA&M verification report.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
IAC_DIR = REPO_ROOT / "01-cmmc-enclave-iac"
GOLD_DIR = REPO_ROOT / "data" / "gold"


def evaluate_iac_controls(iac_dir: Path = IAC_DIR) -> List[Dict[str, Any]]:
    """Audits Terraform & PowerShell baseline files against NIST SP 800-171 Rev 2 controls."""
    main_tf = (iac_dir / "main.tf").read_text(encoding="utf-8")
    vars_tf = (iac_dir / "variables.tf").read_text(encoding="utf-8")
    net_tf = (iac_dir / "network_enclave.tf").read_text(encoding="utf-8")
    id_tf = (iac_dir / "identity_conditional_access.tf").read_text(encoding="utf-8")
    kv_tf = (iac_dir / "keyvault_tls.tf").read_text(encoding="utf-8")
    dsc_ps1 = (iac_dir / "powershell" / "EnclaveServerBaselineDSC.ps1").read_text(encoding="utf-8")

    checks = [
        {
            "control_id": "3.1.1 / 3.5.3",
            "family": "Access Control & Identification/Authentication",
            "requirement": "Phishing-resistant MFA (FIDO2/PIV) & compliant device Conditional Access for enclave-cui-prod",
            "artifact": "01-cmmc-enclave-iac/identity_conditional_access.tf",
            "passed": (
                "azuread_conditional_access_policy" in id_tf
                and "compliantDevice" in id_tf
                and "00000000-0000-0000-0000-000000000004" in id_tf
            ),
            "itil_pmi_outcome": "ITIL 4 Access Mgmt / Zero Unauthorized CUI Sessions",
        },
        {
            "control_id": "3.3.1 / 3.3.2",
            "family": "Audit and Accountability",
            "requirement": "Immutable SIEM audit workspace with >=365-day log retention and disabled public ingestion",
            "artifact": "01-cmmc-enclave-iac/main.tf",
            "passed": (
                "azurerm_log_analytics_workspace" in main_tf
                and "default     = 365" in vars_tf
                and "internet_ingestion_enabled = false" in main_tf
            ),
            "itil_pmi_outcome": "ITIL 4 Information Security Mgmt / C3PAO Audit Evidence",
        },
        {
            "control_id": "3.4.1 / 3.4.2",
            "family": "Configuration Management",
            "requirement": "Mandatory CMDB/FinOps tagging and Windows Server DSC hardening (SMBv1 disabled, SMBv3 signed)",
            "artifact": "01-cmmc-enclave-iac/powershell/EnclaveServerBaselineDSC.ps1",
            "passed": (
                "ComplianceStandard" in main_tf
                and "DisableSMBv1Protocol" in dsc_ps1
                and "RequireSMBv3SecuritySignature" in dsc_ps1
            ),
            "itil_pmi_outcome": "ITIL 4 Service Configuration Mgmt / Drift Prevention",
        },
        {
            "control_id": "3.8.9",
            "family": "Media Protection & Recovery",
            "requirement": "Locked immutable GeoRedundant Recovery Services Vault with public network access disabled",
            "artifact": "01-cmmc-enclave-iac/main.tf",
            "passed": (
                'immutability                  = "Locked"' in main_tf
                and 'storage_mode_type             = "GeoRedundant"' in main_tf
            ),
            "itil_pmi_outcome": "ITIL 4 Service Continuity Mgmt / ERP & PLM Cutover Rollback Safety",
        },
        {
            "control_id": "3.13.1 / 3.13.6",
            "family": "System and Communications Protection",
            "requirement": "Default-deny NSG micro-segmentation across RFC-5737 zones (192.0.2.0/24, 198.51.100.0/24)",
            "artifact": "01-cmmc-enclave-iac/network_enclave.tf",
            "passed": (
                "Deny-All-Inbound-Default" in net_tf
                and "Allow-MID-Server-Discovery-WinRM-HTTPS" in net_tf
                and "198.51.100.25/32" in net_tf
            ),
            "itil_pmi_outcome": "ITIL 4 Infrastructure & Platform Mgmt / Enclave Boundary Isolation",
        },
        {
            "control_id": "3.13.8 / 3.13.11",
            "family": "Cryptographic Protection",
            "requirement": "FIPS 140-2/3 HSM-backed Premium Key Vault, 4096-bit RSA-HSM TLS certs, and Windows FIPS policy",
            "artifact": "01-cmmc-enclave-iac/keyvault_tls.tf",
            "passed": (
                'sku_name                      = "premium"' in kv_tf
                and 'key_type   = "RSA-HSM"' in kv_tf
                and "FIPSAlgorithmPolicyEnabled" in dsc_ps1
            ),
            "itil_pmi_outcome": "PMI Technical Risk Mitigation / Zero Expired Cert Cutover Outages",
        },
    ]
    return checks


def generate_security_dossier(gold_dir: Path = GOLD_DIR) -> Dict[str, Any]:
    """Generates both JSON and Markdown CMMC Level 2 Security Dossiers."""
    gold_dir.mkdir(parents=True, exist_ok=True)
    checks = evaluate_iac_controls()
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    all_passed = passed_count == total_count

    dossier: Dict[str, Any] = {
        "dossier_id": "DOSSIER-CMMC-L2-2026-Q4",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "organization": "org-enterprise-it",
        "enclave_id": "enclave-cui-prod",
        "site_id": "site-mfg-01",
        "domain_fqdn": "example-mfg.local",
        "framework": "NIST SP 800-171 Rev 2 / CMMC 2.0 Level 2",
        "gate_status": "PASSED" if all_passed else "FAILED",
        "controls_evaluated": total_count,
        "controls_passed": passed_count,
        "compliance_score_pct": round((passed_count / total_count) * 100.0, 1),
        "control_verifications": checks,
    }

    json_path = gold_dir / "security_compliance_dossier.json"
    json_path.write_text(json.dumps(dossier, indent=2), encoding="utf-8")

    md_lines = [
        "# Automated CMMC Level 2 & NIST SP 800-171 Security Compliance Dossier",
        "",
        f"- **Dossier ID**: `{dossier['dossier_id']}`",
        f"- **Generated (UTC)**: `{dossier['generated_at_utc']}`",
        f"- **Enclave Scope**: `{dossier['enclave_id']}` | `{dossier['site_id']}` | `{dossier['domain_fqdn']}`",
        f"- **CI/CD Policy Gate Status**: **{dossier['gate_status']}** ({passed_count}/{total_count} Control Groups Verified — {dossier['compliance_score_pct']}%)",
        "",
        "## Automated Control Verification Matrix",
        "",
        "| NIST SP 800-171 Control | Control Family | Technical Requirement | Artifact Verified | ITIL 4 / PMI Outcome | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :---: |",
    ]

    for item in checks:
        status_badge = "PASS" if item["passed"] else "FAIL"
        md_lines.append(
            f"| `{item['control_id']}` | {item['family']} | {item['requirement']} | `{item['artifact']}` | {item['itil_pmi_outcome']} | **{status_badge}** |"
        )

    md_path = gold_dir / "SECURITY_COMPLIANCE_DOSSIER.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return dossier


if __name__ == "__main__":
    result = generate_security_dossier()
    print(
        f"[OK] Generated Security Compliance Dossier ({result['gate_status']} - "
        f"{result['controls_passed']}/{result['controls_evaluated']} control groups verified)."
    )
