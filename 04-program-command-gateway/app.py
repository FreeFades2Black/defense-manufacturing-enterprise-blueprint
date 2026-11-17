#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        04-program-command-gateway/app.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.4.1 (CMDB Baseline), 3.11.1 (Risk Register),
                 3.12.1 (Security Assessment), 3.12.3 (Continuous Monitoring)
ITIL 4 / PMI:    ITIL 4 Release & Continual Improvement Mgmt |
                 PMI Earned Value Management (CPI/SPI), RAID & Cutover Control
================================================================================

Streamlit / Databricks App Operational Control Plane for Defense Manufacturing
Enterprise Modernization (IFS Cloud ERP, Aras Innovator PLM, CMMC Level 2).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from metrics_engine import ensure_all_gold_artifacts  # noqa: E402


def render_app() -> None:
    st.set_page_config(
        page_title="Defense Manufacturing Transformation & CMMC L2 Control Plane",
        layout="wide",
    )

    state = ensure_all_gold_artifacts()
    evm = state["portfolio_evm"]
    med = state["medallion"]
    sec = state["security_dossier"]
    fin = state["finops_gate"]
    cut = state["cutover_summary"]

    st.title("Defense Manufacturing Enterprise Blueprint — Command Gateway")
    st.caption(
        "Sanitized Scope: `org-enterprise-it` | `enclave-cui-prod (192.0.2.0/24)` | "
        "`site-mfg-01 (198.51.100.0/24)` | `example-mfg.local` | NIST SP 800-171 Rev 2 / CMMC Level 2"
    )

    # Top-level Executive KPI Strip
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric(
        "Portfolio CPI (Cost)",
        f"{evm['portfolio_cpi']:.2f}",
        f"${evm['cost_variance_usd']:+,}",
    )
    col2.metric(
        "Portfolio SPI (Schedule)",
        f"{evm['portfolio_spi']:.2f}",
        f"${evm['schedule_variance_usd']:+,}",
    )
    col3.metric(
        "90d Ticket Ping-Pong (>=3 Hops)",
        f"{med['incident_kpis']['ping_pong_rate_pct']}%",
        f"{med['incident_kpis']['ping_pong_ticket_count']} tickets",
        delta_color="inverse",
    )
    col4.metric(
        "CMDB Orphan CI Rate",
        f"{med['cmdb_and_mid_kpis']['orphan_ci_rate_pct']}%",
        f"{med['cmdb_and_mid_kpis']['orphan_ci_count']} CIs unmapped",
        delta_color="inverse",
    )
    col5.metric(
        "CMMC L2 Policy Gate",
        f"{sec['compliance_score_pct']}%",
        sec["gate_status"],
    )
    col6.metric(
        "ERP/PLM Cutover Readiness",
        f"{cut['ready_gates']}/{cut['total_gates']} Gates",
        f"{cut['readiness_pct']}%",
    )

    tab_evm, tab_telemetry, tab_raid, tab_cutover = st.tabs(
        [
            "1. Earned Value (CPI/SPI) & FinOps",
            "2. Week-1 ITSM & CMDB Telemetry (Medallion)",
            "3. RAID Risk Register & 30-Day Roadmap",
            "4. ERP/PLM Cutover & CMMC L2 Security Dossier",
        ]
    )

    with tab_evm:
        st.subheader("Enterprise Transformation Workstreams — Earned Value Management")
        ws_df = pd.DataFrame(state["program"]["workstreams"])
        st.dataframe(ws_df, use_container_width=True)

        st.subheader("Continuous FinOps & Infracost Cloud Guardrail (`03-policy-as-code-governance`)")
        f1, f2, f3 = st.columns(3)
        f1.metric("Approved Enclave Budget Ceiling", f"${fin['approved_monthly_budget_usd']:,.2f}/mo")
        f2.metric(
            "Proposed Monthly Cloud Run-Rate",
            f"${fin['proposed_monthly_cost_usd']:,.2f}/mo",
            f"+{fin['monthly_cost_delta_pct']}% vs baseline",
        )
        f3.metric("FinOps Gate Verdict", fin["finops_gate_status"], f"${fin['budget_headroom_usd']:,.2f} headroom")
        st.dataframe(pd.DataFrame(fin["resource_breakdown"]), use_container_width=True)

    with tab_telemetry:
        st.subheader("Gold Layer: 80/20 Pareto Ranking of ServiceNow Queue Friction (90-Day Window)")
        st.markdown(
            "> **Ground-Truth Finding**: Multi-hop reassignments (`Corp-IT-Tier1 -> Site-MFG-01-IT -> Enclave-SecOps`) "
            "on **GCC High MFA provisioning** and **IFS Cloud ERP role entitlements** drive over **55%** of total queue hours."
        )
        pareto_df = pd.DataFrame(med["top_pareto_bottlenecks"])
        st.dataframe(pareto_df, use_container_width=True)

        st.subheader("CMDB & ServiceNow MID Server Health (`mid-mfg-01.example-mfg.local`)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Audited Server CIs", med["cmdb_and_mid_kpis"]["total_server_cis"])
        c2.metric(
            "MID Server WinRM-5986 Timeout Rate",
            f"{med['cmdb_and_mid_kpis']['mid_discovery_failure_rate_pct']}%",
        )
        c3.metric(
            "Enclave OS Patch Compliance",
            f"{med['cmdb_and_mid_kpis']['os_patch_compliance_pct']}%",
        )

    with tab_raid:
        st.subheader("Active Program RAID Register (Mapped to NIST SP 800-171 Controls)")
        raid_df = pd.DataFrame(state["program"]["raid_register"])
        st.dataframe(raid_df, use_container_width=True)

    with tab_cutover:
        st.subheader(f"ERP / PLM Production Cutover Readiness — Verdict: `{cut['overall_go_no_go']}`")
        cut_df = pd.DataFrame(state["program"]["cutover_readiness_checklist"])
        st.dataframe(cut_df, use_container_width=True)

        st.subheader("Automated CMMC Level 2 & NIST SP 800-171 Verification Dossier")
        sec_df = pd.DataFrame(sec["control_verifications"])
        st.dataframe(sec_df, use_container_width=True)


if __name__ == "__main__":
    render_app()
