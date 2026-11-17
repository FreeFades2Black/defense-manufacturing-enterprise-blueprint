#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        02-itsm-medallion-telemetry/pipeline.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.3.1 (Audit Review & Analysis), 3.4.1 (CMDB Baseline Inventory),
                 3.11.1 (Risk Assessment), 3.12.3 (Continuous Monitoring)
ITIL 4 / PMI:    ITIL 4 Incident Mgmt, Service Request Mgmt, Continual Improvement |
                 PMI Week-1 Bottleneck Quantification & Pareto Prioritization
================================================================================

Executable Bronze -> Silver -> Gold Medallion Telemetry Pipeline.
Processes 90-day ServiceNow Incident, Requested Item (sc_req_item), Catalog Task
(sc_task), Change Request (change_request), Audit Trail (sys_audit), and CMDB
datasets to surface:
1. Multi-hop ticket "ping-ponging" across Corporate IT, Site IT, and SecOps.
2. Exact queue dwell hours per assignment group transition from sys_audit.
3. The top 20% of ticket subcategories driving ~80% of total queue friction.
4. CMDB orphan rates and ServiceNow MID Server discovery credential failures.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
GOLD_DIR = REPO_ROOT / "data" / "gold"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_synthetic_telemetry import generate_all  # noqa: E402


def run_medallion_pipeline(
    raw_dir: Path = RAW_DIR,
    gold_dir: Path = GOLD_DIR,
) -> Dict[str, Any]:
    """Executes Bronze -> Silver -> Gold transformations and writes Gold analytical artifacts."""
    if not (raw_dir / "servicenow_sys_audit_90d.csv").exists():
        generate_all(raw_dir)

    gold_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # BRONZE LAYER: Load raw 90-day ServiceNow (incident, sc_req_item, sc_task,
    # change_request, sys_audit) & CMDB extracts
    # -------------------------------------------------------------------------
    inc_df = pd.read_csv(raw_dir / "servicenow_incidents_90d.csv")
    ritm_df = pd.read_csv(raw_dir / "servicenow_sc_req_item_90d.csv")
    sc_df = pd.read_csv(raw_dir / "servicenow_sc_tasks_90d.csv")
    chg_df = pd.read_csv(raw_dir / "servicenow_change_requests_90d.csv")
    audit_df = pd.read_csv(raw_dir / "servicenow_sys_audit_90d.csv")
    cmdb_df = pd.read_csv(raw_dir / "cmdb_ci_inventory.csv")

    # -------------------------------------------------------------------------
    # SILVER LAYER: Enrich Incidents with CMDB CI metadata & sys_audit hop counts
    # -------------------------------------------------------------------------
    audit_hop_Rollup = (
        audit_df.groupby("documentkey", as_index=False)
        .agg(
            verified_audit_hops=("audit_sys_id", "count"),
            audit_dwell_hours=("dwell_hours_before_transfer", "sum"),
        )
    )

    silver_inc = inc_df.merge(
        cmdb_df[["ci_name", "is_orphan_ci", "mid_discovery_status", "os_patch_compliant"]],
        left_on="cmdb_ci",
        right_on="ci_name",
        how="left",
    ).merge(
        audit_hop_Rollup,
        left_on="number",
        right_on="documentkey",
        how="left",
    )
    silver_inc["verified_audit_hops"] = silver_inc["verified_audit_hops"].fillna(0).astype(int)
    silver_inc["audit_dwell_hours"] = silver_inc["audit_dwell_hours"].fillna(0.0).round(2)
    silver_inc["is_ping_pong_ticket"] = silver_inc["reassignment_count"] >= 3
    silver_inc.to_csv(gold_dir / "silver_enriched_incidents.csv", index=False)

    # Gold Layer: Queue Handoff Matrix from sys_audit
    handoff_df = (
        audit_df.groupby(["oldvalue", "newvalue"], as_index=False)
        .agg(
            transfer_count=("audit_sys_id", "count"),
            avg_dwell_hours_before_transfer=("dwell_hours_before_transfer", "mean"),
            total_dwell_hours_lost=("dwell_hours_before_transfer", "sum"),
        )
        .sort_values(by="total_dwell_hours_lost", ascending=False)
        .reset_index(drop=True)
    )
    handoff_df["avg_dwell_hours_before_transfer"] = handoff_df["avg_dwell_hours_before_transfer"].round(2)
    handoff_df["total_dwell_hours_lost"] = handoff_df["total_dwell_hours_lost"].round(2)
    handoff_df.to_csv(gold_dir / "gold_sys_audit_handoff_matrix.csv", index=False)

    # -------------------------------------------------------------------------
    # GOLD LAYER: Pareto 80/20 Bottleneck Analysis & Executive KPIs
    # -------------------------------------------------------------------------
    pareto_df = (
        silver_inc.groupby(["category", "subcategory", "assignment_group_path"], as_index=False)
        .agg(
            ticket_count=("number", "count"),
            avg_hops=("reassignment_count", "mean"),
            avg_mttr_hours=("mttr_hours", "mean"),
            total_mttr_hours=("mttr_hours", "sum"),
            sla_breach_count=("sla_breached", "sum"),
            ping_pong_count=("is_ping_pong_ticket", "sum"),
        )
        .sort_values(by="total_mttr_hours", ascending=False)
        .reset_index(drop=True)
    )

    pareto_df["avg_hops"] = pareto_df["avg_hops"].round(2)
    pareto_df["avg_mttr_hours"] = pareto_df["avg_mttr_hours"].round(2)
    pareto_df["total_mttr_hours"] = pareto_df["total_mttr_hours"].round(2)
    pareto_df["sla_breach_rate_pct"] = (
        (pareto_df["sla_breach_count"] / pareto_df["ticket_count"]) * 100.0
    ).round(1)

    grand_total_mttr = float(pareto_df["total_mttr_hours"].sum())
    pareto_df["share_of_total_mttr_pct"] = (
        (pareto_df["total_mttr_hours"] / grand_total_mttr) * 100.0
    ).round(1)
    pareto_df["cumulative_mttr_pct"] = (
        pareto_df["total_mttr_hours"].cumsum() / grand_total_mttr * 100.0
    ).round(1)
    pareto_df["is_top_pareto_driver"] = pareto_df["cumulative_mttr_pct"] <= 82.0

    pareto_df.to_csv(gold_dir / "gold_pareto_bottlenecks.csv", index=False)

    # Catalog Request Item (sc_req_item) & Task Automation Potential Summary
    sc_summary_df = (
        sc_df.groupby(["catalog_item", "category", "automation_candidate"], as_index=False)
        .agg(
            request_count=("sc_task_number", "count"),
            avg_hops=("reassignment_count", "mean"),
            avg_fulfillment_hours=("fulfillment_hours", "mean"),
            sla_breach_count=("sla_breached", "sum"),
        )
        .sort_values(by="avg_fulfillment_hours", ascending=False)
    )
    sc_summary_df["avg_hops"] = sc_summary_df["avg_hops"].round(2)
    sc_summary_df["avg_fulfillment_hours"] = sc_summary_df["avg_fulfillment_hours"].round(2)
    sc_summary_df.to_csv(gold_dir / "gold_catalog_automation_candidates.csv", index=False)

    total_incidents = int(len(silver_inc))
    ping_pong_incidents = int(silver_inc["is_ping_pong_ticket"].sum())
    sla_breaches = int(silver_inc["sla_breached"].sum())

    total_cis = int(len(cmdb_df))
    orphan_cis = int(cmdb_df["is_orphan_ci"].sum())
    mid_failures = int((cmdb_df["mid_discovery_status"] != "Success").sum())
    patch_compliant_cis = int(cmdb_df["os_patch_compliant"].sum())

    summary_payload: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": {
            "organization": "org-enterprise-it",
            "site_id": "site-mfg-01",
            "enclave_id": "enclave-cui-prod",
            "domain": "example-mfg.local",
        },
        "incident_kpis": {
            "total_incidents_90d": total_incidents,
            "ping_pong_ticket_count": ping_pong_incidents,
            "ping_pong_rate_pct": round((ping_pong_incidents / total_incidents) * 100.0, 1),
            "sla_breach_count": sla_breaches,
            "sla_breach_rate_pct": round((sla_breaches / total_incidents) * 100.0, 1),
            "overall_avg_mttr_hours": round(float(silver_inc["mttr_hours"].mean()), 2),
            "sys_audit_transitions_logged": int(len(audit_df)),
        },
        "catalog_task_kpis": {
            "total_sc_req_items_90d": int(len(ritm_df)),
            "total_sc_tasks_90d": int(len(sc_df)),
            "ping_pong_ritm_rate_pct": round(float(ritm_df["is_ping_pong_ritm"].mean()) * 100.0, 1),
            "automation_candidate_pct": round(
                float(sc_df["automation_candidate"].mean()) * 100.0, 1
            ),
            "avg_fulfillment_hours": round(float(sc_df["fulfillment_hours"].mean()), 2),
        },
        "change_kpis": {
            "total_changes_90d": int(len(chg_df)),
            "standard_change_pct": round(
                float((chg_df["change_type"] == "Standard").mean()) * 100.0, 1
            ),
            "normal_change_avg_cab_wait_hours": round(
                float(chg_df.loc[chg_df["change_type"] == "Normal", "cab_lead_time_hours"].mean()),
                1,
            ),
            "change_success_rate_pct": round(
                float(chg_df["change_successful"].mean()) * 100.0, 1
            ),
        },
        "cmdb_and_mid_kpis": {
            "total_server_cis": total_cis,
            "orphan_ci_count": orphan_cis,
            "orphan_ci_rate_pct": round((orphan_cis / total_cis) * 100.0, 1),
            "mid_discovery_failure_count": mid_failures,
            "mid_discovery_failure_rate_pct": round((mid_failures / total_cis) * 100.0, 1),
            "os_patch_compliance_pct": round((patch_compliant_cis / total_cis) * 100.0, 1),
        },
        "top_pareto_bottlenecks": pareto_df.to_dict(orient="records"),
        "sys_audit_handoff_matrix": handoff_df.to_dict(orient="records"),
    }

    summary_path = gold_dir / "medallion_gold_summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    return summary_payload


if __name__ == "__main__":
    result = run_medallion_pipeline()
    inc_kpis = result["incident_kpis"]
    cmdb_kpis = result["cmdb_and_mid_kpis"]
    print("[OK] Medallion Lakehouse Pipeline (Bronze -> Silver -> Gold) Completed:")
    print(
        f"  - 90d Incidents Analyzed : {inc_kpis['total_incidents_90d']} "
        f"(Ping-Pong Rate >=3 hops: {inc_kpis['ping_pong_rate_pct']}%, "
        f"sys_audit Transitions: {inc_kpis['sys_audit_transitions_logged']})"
    )
    print(
        f"  - CMDB Server CIs Audited: {cmdb_kpis['total_server_cis']} "
        f"(Orphan CI Rate: {cmdb_kpis['orphan_ci_rate_pct']}%, "
        f"MID Server Discovery Timeout Rate: {cmdb_kpis['mid_discovery_failure_rate_pct']}%)"
    )
