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
Designed for single-screen executive command demos on Omarchy Linux.
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
        initial_sidebar_state="collapsed",
    )

    state = ensure_all_gold_artifacts()
    evm = state["portfolio_evm"]
    med = state["medallion"]
    sec = state["security_dossier"]
    fin = state["finops_gate"]
    cut = state["cutover_summary"]

    st.title("Defense Manufacturing Enterprise Blueprint — Operational Command Gateway")
    st.caption(
        "Sanitized Scope: `org-enterprise-it` | `enclave-cui-prod (192.0.2.0/24)` | "
        "`site-mfg-01 (198.51.100.0/24)` | `example-mfg.local` | NIST SP 800-171 Rev 2 / CMMC Level 2"
    )

    # Top-level Executive KPI Strip
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric(
        "Portfolio CPI (Cost)",
        f"{evm['portfolio_cpi']:.2f}",
        f"${evm['cost_variance_usd']:+,} CV",
    )
    col2.metric(
        "Portfolio SPI (Schedule)",
        f"{evm['portfolio_spi']:.2f}",
        f"${evm['schedule_variance_usd']:+,} SV",
    )
    col3.metric(
        "90d Ping-Pong Rate (>=3 Hops)",
        f"{med['incident_kpis']['ping_pong_rate_pct']}%",
        f"{med['incident_kpis']['sys_audit_transitions_logged']} sys_audit hops",
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
        f"{sec['gate_status']} ({sec['controls_passed']}/{sec['controls_evaluated']})",
    )
    col6.metric(
        "ERP/PLM Cutover Readiness",
        f"{cut['ready_gates']}/{cut['total_gates']} Gates",
        f"{cut['readiness_pct']}%",
    )

    st.divider()

    # Visual Charts Row: Workstream CPI/SPI vs 80/20 Pareto MTTR Friction Hours
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("**Earned Value Index Comparison (`CPI` vs `SPI` by Workstream)**")
        ws_chart_df = pd.DataFrame(state["program"]["workstreams"])[
            ["workstream_id", "cpi", "spi"]
        ].set_index("workstream_id")
        st.bar_chart(ws_chart_df, height=210)

    with chart_right:
        st.markdown("**80/20 Pareto Queue Friction (`Total MTTR Hours` by Subcategory)**")
        pareto_chart_df = pd.DataFrame(med["top_pareto_bottlenecks"])[
            ["subcategory", "total_mttr_hours"]
        ].set_index("subcategory")
        st.bar_chart(pareto_chart_df, height=210)

    # Single-Screen Executive Command Quadrant (2x2 Grid)
    left_top, right_top = st.columns(2)

    with left_top:
        st.subheader("1. Earned Value (CPI / SPI) — ERP, PLM & Enclave Workstreams")
        ws_df = pd.DataFrame(state["program"]["workstreams"])[
            ["workstream_id", "name", "cpi", "spi", "planned_value_usd", "earned_value_usd", "actual_cost_usd", "status"]
        ]
        st.dataframe(ws_df, use_container_width=True, hide_index=True)

    with right_top:
        st.subheader("2. Gold Layer: 80/20 Pareto Bottlenecks (`incident` + `sys_audit`)")
        pareto_df = pd.DataFrame(med["top_pareto_bottlenecks"])[
            ["subcategory", "ticket_count", "avg_hops", "avg_mttr_hours", "sla_breach_rate_pct", "cumulative_mttr_pct"]
        ]
        st.dataframe(pareto_df, use_container_width=True, hide_index=True)

    left_bottom, right_bottom = st.columns(2)

    with left_bottom:
        st.subheader("3. Active Program RAID Register (NIST SP 800-171 Mapped)")
        raid_df = pd.DataFrame(state["program"]["raid_register"])[
            ["id", "type", "severity", "title", "nist_control", "target_closure_days"]
        ]
        st.dataframe(raid_df, use_container_width=True, hide_index=True)

    with right_bottom:
        st.subheader(f"4. ERP/PLM Cutover Readiness & CMMC Gate (`{cut['overall_go_no_go']}`)")
        cut_df = pd.DataFrame(state["program"]["cutover_readiness_checklist"])[
            ["gate_id", "category", "criterion", "nist_control", "ready"]
        ]
        st.dataframe(cut_df, use_container_width=True, hide_index=True)

    with st.expander("Drilldown: ServiceNow `sys_audit` Queue Handoff Matrix & FinOps Infracost Breakdown"):
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("**`sys_audit` Multi-Hop Queue Transfer Matrix**")
            st.dataframe(pd.DataFrame(med.get("sys_audit_handoff_matrix", [])), use_container_width=True, hide_index=True)
        with d2:
            st.markdown(
                f"**Infracost Monthly Cloud Guardrail**: `${fin['proposed_monthly_cost_usd']:,.2f}/mo` "
                f"vs `${fin['approved_monthly_budget_usd']:,.2f}/mo` budget (`{fin['finops_gate_status']}`)"
            )
            st.dataframe(pd.DataFrame(fin["resource_breakdown"]), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_app()
