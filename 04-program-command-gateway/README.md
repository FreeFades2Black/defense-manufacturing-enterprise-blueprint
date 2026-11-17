<!--
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        04-program-command-gateway/README.md
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.4.1, 3.11.1, 3.12.1, 3.12.3, 3.12.4
ITIL 4 / PMI:    ITIL 4 Release & Deployment Mgmt, Continual Improvement |
                 PMI Earned Value Management (CPI/SPI), RAID & Cutover Control
================================================================================
-->

# Module 04: Transformation & Readiness Control Plane (`04-program-command-gateway`)

This module provides the **Streamlit / Databricks App Operational Command Gateway** uniting executive program governance (**Earned Value CPI/SPI**, **RAID Register**, **ERP/PLM Cutover Readiness**) with hard engineering telemetry from the **Medallion Lakehouse** and **CMMC Level 2 Policy-as-Code Gate**.

## Views Included in the Gateway

1. **Program Earned Value (CPI / SPI) & FinOps Guardrails**:
   - Real-time portfolio and workstream $PV$, $EV$, $AC$, $CPI$, and $SPI$ tracking across **IFS Cloud ERP**, **Aras Innovator PLM**, **CMMC Level 2 Enclave IaC**, and **GCC High / ServiceNow Orchestration**.
2. **Week-1 Ground-Truth Telemetry & 80/20 Pareto Queue Bottlenecks**:
   - Interactive visualization of the top 20% of ServiceNow subcategories driving >80% of total MTTR hours, multi-hop ticket "ping-ponging" (`reassignment_count >= 3`), CMDB orphan CI rates, and MID Server discovery timeouts.
3. **RAID Risk Register & Day-10 Alignment Roadmap**:
   - Active Risks, Assumptions, Issues, and Dependencies mapped to NIST SP 800-171 controls and 30-day engineering mitigations.
4. **ERP/PLM Cutover Readiness Gate & CMMC Level 2 Security Dossier**:
   - Go/No-Go cutover checklist and live NIST SP 800-171 control verification dossier.

## Running Locally or on Databricks Apps

```bash
# Local Streamlit execution
streamlit run 04-program-command-gateway/app.py
```
