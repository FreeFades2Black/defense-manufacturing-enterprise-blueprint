<!--
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        docs/DAY1_EXECUTION_PLAYBOOK.md
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.12.1 (Security Assessment), 3.12.3 (Continuous Monitoring),
                 3.1.1 (Authorized Access Control), 3.4.1 (System Baseline)
ITIL 4 / PMI:    ITIL 4 Continual Improvement & Service Configuration Mgmt |
                 PMI PMBOK Stakeholder Engagement & Scope Baseline Verification
================================================================================
-->

# Day-1 to Day-10 Operational Execution Playbook: "Request for Access, Pull for Truth"

This playbook operationalizes the first 10 business days for a hybrid **Technical Program Manager / Senior Systems Engineer** entering a DoD-regulated manufacturing enterprise (`site-mfg-01` / `enclave-cui-prod`).

---

## 1. Days 1–2: Stakeholder Access & Governance Document Requests

### 1.1 Corporate ServiceNow / ITSM Platform Admins (`org-enterprise-it`)
- **Role / Entitlement Request**:
  - `itil` read/write operational role scoped to `site-mfg-01` and `enclave-cui-prod` assignment groups (`Site-MFG-01-IT`, `Enclave-SecOps`, `ERP-Platform-Team`, `PLM-Engineering-Support`).
  - `pa_viewer` / Performance Analytics reporting access for 90-day queue trend analysis.
  - Scoped read-only service principal (`svc-snow-telemetry-ro@example-mfg.local`) with Table API (`GET`) permissions on:
    - `incident`
    - `sc_req_item` and `sc_task`
    - `change_request`
    - `sys_audit` (filtered to assignment group transitions)
    - `cmdb_ci_server` and `cmdb_rel_ci`
    - `ecc_agent_log` (MID Server logs for `mid-mfg-01.example-mfg.local`)
- **Governance Guardrail**: Explicitly state that zero global workflow changes will be requested prior to the Day-10 empirical data review.

### 1.2 Corporate Information Security & Enclave ISSMs (`enclave-cui-prod`)
- **Artifact Request Checklist**:
  - Current **System Security Plan (SSP)** for `enclave-cui-prod` covering all 110 NIST SP 800-171 Rev 2 controls.
  - Active **Plan of Action & Milestones (POA&M)** with target closure dates and SPRS score impact calculations.
  - **Shared Responsibility Matrix (SRM)** delineating Corporate IT (`org-enterprise-it`), Enclave Operations (`enclave-cui-prod`), and Cloud Service Provider (Azure Government / GCC High) boundaries.

### 1.3 Corporate Infrastructure & Network Engineering
- **Artifact & Access Request Checklist**:
  - Read-only Auditor access to Hyper-V / VMware vSphere clusters hosting `site-mfg-01` workloads (`192.0.2.0/24`).
  - Current firewall rule tables and perimeter diagrams between `192.0.2.0/24` (`enclave-cui-prod`), `198.51.100.0/24` (`site-mfg-01` OT/MES DMZ), and `203.0.113.0/24` (`org-enterprise-it` corporate transit).
  - Active Directory (`example-mfg.local`) and Entra ID (GCC High) Global Reader role for non-destructive hygiene auditing.

### 1.4 ERP/PLM Vendors & PMO Leads
- **Artifact Request Checklist**:
  - Executed **Statements of Work (SOWs)** and vendor deliverable milestones for **IFS Cloud** (ERP) and **Aras Innovator** (PLM).
  - Integrated Master Schedule (IMS) with critical path dependencies.
  - Current **Earned Value Management (EVM)** baseline: Planned Value ($PV$), Earned Value ($EV$), Actual Cost ($AC$), Cost Performance Index ($CPI = EV / AC$), and Schedule Performance Index ($SPI = EV / PV$).
  - Active **RAID Register** (Risks, Assumptions, Issues, Dependencies).

---

## 2. Days 3–7: Direct Telemetry Extraction & Medallion Ingestion

Execute the following commands once read-only credentials are granted:

### Step A: Active Directory, Entra ID & Windows Server Baseline Discovery
```powershell
# Run non-destructive read-only enclave discovery
pwsh -File .\01-cmmc-enclave-iac\powershell\Invoke-EnclaveReadOnlyDiscovery.ps1 `
    -DomainFqdn "example-mfg.local" `
    -EnclaveSubnet "192.0.2.0/24" `
    -OutputPath ".\data\raw\ad_server_discovery_snapshot.json"

# Verify TLS 1.2/1.3 & FIPS certificate lifecycle across Enclave endpoints
pwsh -File .\01-cmmc-enclave-iac\powershell\Test-TlsCertificateLifecycle.ps1 `
    -WarningDays 30
```

### Step B: Ingest 90-Day ServiceNow & CMDB Exports into Medallion Pipeline
```bash
# 1. Generate or load 90-day raw exports into data/raw/
python scripts/generate_synthetic_telemetry.py

# 2. Run Bronze -> Silver -> Gold Medallion transformations
python 02-itsm-medallion-telemetry/pipeline.py
```

### Step C: Key Diagnostic Indicators Computed Automatically
1. **Multi-Hop "Ping-Pong" Ratio**: Percentage of tickets with `reassignment_count >= 3` cycling between `Corp-IT-Tier1`, `Site-MFG-01-IT`, and `Enclave-SecOps`.
2. **80/20 Pareto Bottleneck Ranking**: Identification of the top 20% subcategories responsible for >80% of total MTTR hours and SLA breaches.
3. **CMDB Orphan & Stale CI Rate**: Percentage of `site-mfg-01` and `enclave-cui-prod` servers missing upstream application relationships or failing MID Server WMI/WinRM discovery on `192.0.2.0/24`.

---

## 3. Day 10: Executive & Engineering Alignment Briefing Agenda

1. **Executive Summary (5 mins)**:
   - Cross-reference official SSP/POA&M and PMO SOW schedules against empirical Week-1 telemetry.
2. **ITSM Flow & Provisioning Bottlenecks (10 mins)**:
   - Present Gold Layer Pareto chart showing multi-hop reassignment latency across GCC High / Entra ID access requests and ERP role provisioning.
   - Propose automated Standard Changes + PowerShell/REST orchestration for top 3 high-volume catalog items.
3. **CMDB & Infrastructure Cutover Readiness (10 mins)**:
   - Review compute/storage headroom and MID Server credential timeout remediation on `192.0.2.0/24` ahead of IFS Cloud / Aras Innovator cutover.
4. **CMMC Level 2 & FinOps Guardrails (10 mins)**:
   - Demonstrate automated OPA/Rego policy checks and Infracost PR gates preventing unbudgeted cloud spend and POA&M regression.
5. **30-Day Quick-Win Commitment & Sign-Off (10 mins)**:
   - Lock in 3 measurable 30-day targets:
     - Reduce multi-hop ticket reassignment rate by **40%**.
     - Remediate **100%** of expiring TLS certificates and orphaned Tier-1 ERP/PLM CIs.
     - Establish weekly automated EVM ($CPI$/$SPI$) & Cutover Readiness gate tracking via [`04-program-command-gateway/`](../04-program-command-gateway/).
