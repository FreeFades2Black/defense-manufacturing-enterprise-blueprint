#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        scripts/generate_synthetic_telemetry.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.3.1 (Audit Log Generation), 3.4.1 (CMDB Baseline Inventory),
                 3.11.1 (Risk Assessment), 3.12.3 (Continuous Monitoring)
ITIL 4 / PMI:    ITIL 4 Measurement & Reporting, Service Configuration Mgmt |
                 PMI Earned Value Management (CPI/SPI) & RAID Governance
================================================================================

Deterministic synthetic telemetry generator producing 90-day ServiceNow ticket
queues (incident, sc_task, change_request), CMDB Configuration Item (CI) tables
with MID Server discovery status, and ERP/PLM Program EVM/RAID fixtures.
"""

from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

SEED = 20261117

CATEGORIES_AND_PROFILES = [
    {
        "category": "Identity & Access (GCC High / Entra / AD)",
        "subcategory": "GCC-High-MFA-Provisioning",
        "weight": 0.24,
        "hop_range": (3, 6),
        "mttr_range": (28.0, 96.0),
        "sla_hours": 24.0,
        "hop_path": "Corp-IT-Tier1 -> Org-Identity-Ops -> Enclave-SecOps -> Site-MFG-01-IT",
    },
    {
        "category": "ERP / PLM Enterprise Platforms",
        "subcategory": "IFS-ERP-Role-Entitlement",
        "weight": 0.21,
        "hop_range": (3, 5),
        "mttr_range": (24.0, 84.0),
        "sla_hours": 24.0,
        "hop_path": "Corp-IT-Tier1 -> Site-MFG-01-IT -> Enclave-SecOps -> ERP-Platform-Team",
    },
    {
        "category": "ERP / PLM Enterprise Platforms",
        "subcategory": "Aras-PLM-CAD-Vault-Sync",
        "weight": 0.14,
        "hop_range": (2, 4),
        "mttr_range": (14.0, 52.0),
        "sla_hours": 16.0,
        "hop_path": "Site-MFG-01-IT -> Corp-Storage-Team -> PLM-Engineering-Support",
    },
    {
        "category": "CMDB & Discovery Infrastructure",
        "subcategory": "MID-Server-Credential-Timeout",
        "weight": 0.11,
        "hop_range": (2, 5),
        "mttr_range": (18.0, 64.0),
        "sla_hours": 24.0,
        "hop_path": "Corp-IT-Tier1 -> Corp-SNOW-Admins -> Enclave-SecOps -> Site-MFG-01-IT",
    },
    {
        "category": "Network & Enclave Boundary",
        "subcategory": "OT-VLAN-Firewall-Exception",
        "weight": 0.10,
        "hop_range": (2, 4),
        "mttr_range": (16.0, 48.0),
        "sla_hours": 24.0,
        "hop_path": "Site-MFG-01-IT -> Corp-Network-Eng -> Enclave-SecOps",
    },
    {
        "category": "Identity & Access (GCC High / Entra / AD)",
        "subcategory": "PKI-SmartCard-Cert-Renewal",
        "weight": 0.08,
        "hop_range": (1, 2),
        "mttr_range": (4.0, 18.0),
        "sla_hours": 24.0,
        "hop_path": "Site-MFG-01-IT -> Enclave-SecOps",
    },
    {
        "category": "Shop Floor OT / Peripherals",
        "subcategory": "Barcode-Thermal-Printer-Spooler",
        "weight": 0.07,
        "hop_range": (0, 1),
        "mttr_range": (1.5, 8.0),
        "sla_hours": 12.0,
        "hop_path": "Site-MFG-01-IT",
    },
    {
        "category": "End-User Compute",
        "subcategory": "Workstation-Patch-Reboot-Loop",
        "weight": 0.05,
        "hop_range": (0, 1),
        "mttr_range": (2.0, 10.0),
        "sla_hours": 16.0,
        "hop_path": "Site-MFG-01-IT",
    },
]


def generate_cmdb_inventory(rng: random.Random, count: int = 120) -> List[Dict[str, Any]]:
    """Generates sanitized CMDB Server CI records across RFC-5737 subnets."""
    records: List[Dict[str, Any]] = []
    zones = [
        ("enclave-cui-prod", "192.0.2", "IFS Cloud ERP / Aras PLM Core"),
        ("site-mfg-01", "198.51.100", "Shop-Floor MES / MID Server DMZ"),
        ("org-enterprise-it", "203.0.113", "Enterprise Transit / Shared Identity"),
    ]
    os_choices = [
        "Windows Server 2022 Datacenter",
        "Windows Server 2019 Standard",
        "RHEL 8.9 Enterprise",
    ]

    for idx in range(1, count + 1):
        zone_id, subnet_prefix, app_tier = zones[idx % len(zones)]
        host_octet = 10 + (idx % 230)
        ip_addr = f"{subnet_prefix}.{host_octet}"
        ci_name = f"srv-{zone_id.split('-')[0]}-{idx:03d}.example-mfg.local"

        # Simulate realistic MID server credential / WinRM blocks on 22% of CIs
        discovery_failed = rng.random() < 0.22
        upstream_mapped = not (discovery_failed or rng.random() < 0.08)
        patch_compliant = rng.random() > 0.14

        records.append(
            {
                "ci_sys_id": f"CI-{idx:05d}",
                "ci_name": ci_name,
                "ip_address": ip_addr,
                "enclave_zone": zone_id,
                "business_service": app_tier,
                "operating_system": rng.choice(os_choices),
                "operational_status": "Operational",
                "upstream_app_mapped": upstream_mapped,
                "mid_server_agent": "mid-mfg-01.example-mfg.local",
                "mid_discovery_status": (
                    "WinRM-5986-Credential-Timeout" if discovery_failed else "Success"
                ),
                "os_patch_compliant": patch_compliant,
                "is_orphan_ci": not upstream_mapped,
            }
        )
    return records


def generate_incidents_90d(
    rng: random.Random, cmdb_cis: List[Dict[str, Any]], count: int = 450
) -> List[Dict[str, Any]]:
    """Generates 90 days of synthetic ServiceNow incident records with reassignment hops."""
    base_time = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
    weights = [p["weight"] for p in CATEGORIES_AND_PROFILES]
    incidents: List[Dict[str, Any]] = []

    for idx in range(1, count + 1):
        profile = rng.choices(CATEGORIES_AND_PROFILES, weights=weights, k=1)[0]
        opened_offset_days = rng.uniform(0, 90)
        opened_at = base_time - timedelta(days=opened_offset_days)

        hops = rng.randint(*profile["hop_range"])
        mttr_hours = round(rng.uniform(*profile["mttr_range"]) * (1.0 + 0.12 * hops), 2)
        resolved_at = opened_at + timedelta(hours=mttr_hours)
        sla_breached = mttr_hours > profile["sla_hours"]
        linked_ci = rng.choice(cmdb_cis)

        incidents.append(
            {
                "number": f"INC{100000 + idx}",
                "opened_at": opened_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "resolved_at": resolved_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "category": profile["category"],
                "subcategory": profile["subcategory"],
                "priority": rng.choice(["1 - Critical", "2 - High", "3 - Moderate", "3 - Moderate"]),
                "site_id": "site-mfg-01",
                "enclave_id": linked_ci["enclave_zone"],
                "cmdb_ci": linked_ci["ci_name"],
                "reassignment_count": hops,
                "is_ping_pong_ticket": hops >= 3,
                "assignment_group_path": profile["hop_path"],
                "final_assignment_group": profile["hop_path"].split(" -> ")[-1],
                "sla_target_hours": profile["sla_hours"],
                "mttr_hours": mttr_hours,
                "sla_breached": sla_breached,
            }
        )
    return incidents


def generate_sc_tasks_90d(rng: random.Random, count: int = 300) -> List[Dict[str, Any]]:
    """Generates 90 days of ServiceNow Catalog Tasks (sc_task / sc_req_item)."""
    base_time = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
    catalog_items = [
        ("GCC-High-M365-License-And-Enclave-Group", "Identity & Access", True, 42.5),
        ("IFS-Cloud-Shop-Floor-Supervisor-Role", "ERP / PLM Access", True, 38.0),
        ("Aras-Innovator-CUI-Drawing-Vault-Read", "ERP / PLM Access", True, 31.0),
        ("ServiceNow-ITIL-ReadOnly-Reporting-Role", "ITSM Governance", False, 14.0),
        ("Standard-Enclave-VM-Provisioning-Request", "Hybrid Infrastructure", True, 54.0),
    ]
    tasks: List[Dict[str, Any]] = []

    for idx in range(1, count + 1):
        item_name, cat, manual_bottleneck, avg_hrs = rng.choice(catalog_items)
        opened_at = base_time - timedelta(days=rng.uniform(0, 90))
        hops = rng.randint(2, 5) if manual_bottleneck else rng.randint(0, 1)
        fulfillment_hours = round(rng.uniform(avg_hrs * 0.6, avg_hrs * 1.6), 2)

        tasks.append(
            {
                "sc_task_number": f"SCTASK{200000 + idx}",
                "ritm_number": f"RITM{300000 + idx}",
                "opened_at": opened_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "catalog_item": item_name,
                "category": cat,
                "site_id": "site-mfg-01",
                "enclave_id": "enclave-cui-prod",
                "reassignment_count": hops,
                "manual_approval_steps": 4 if manual_bottleneck else 1,
                "fulfillment_hours": fulfillment_hours,
                "sla_breached": fulfillment_hours > 36.0,
                "automation_candidate": manual_bottleneck,
            }
        )
    return tasks


def generate_change_requests_90d(rng: random.Random, count: int = 120) -> List[Dict[str, Any]]:
    """Generates 90 days of ServiceNow Change Requests (change_request)."""
    base_time = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
    change_types = ["Normal", "Standard", "Emergency"]
    changes: List[Dict[str, Any]] = []

    for idx in range(1, count + 1):
        c_type = rng.choices(change_types, weights=[0.55, 0.35, 0.10], k=1)[0]
        opened_at = base_time - timedelta(days=rng.uniform(0, 90))
        cab_wait_hours = (
            round(rng.uniform(48.0, 120.0), 1)
            if c_type == "Normal"
            else round(rng.uniform(1.0, 8.0), 1)
        )
        changes.append(
            {
                "chg_number": f"CHG{400000 + idx}",
                "opened_at": opened_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "change_type": c_type,
                "target_environment": rng.choice(["enclave-cui-prod", "site-mfg-01"]),
                "program_workstream": rng.choice(
                    [
                        "IFS-Cloud-ERP-Cutover",
                        "Aras-PLM-Vault-Migration",
                        "CMMC-L2-Firewall-Hardening",
                        "Windows-Server-Patch-Cycle",
                    ]
                ),
                "cab_lead_time_hours": cab_wait_hours,
                "nist_800_171_impact_assessed": True,
                "change_successful": rng.random() > 0.04,
            }
        )
    return changes


def generate_program_governance_fixture() -> Dict[str, Any]:
    """Generates deterministic Earned Value Management (CPI/SPI), RAID, and Cutover gates."""
    return {
        "program_name": "Defense Manufacturing Enterprise Modernization (ERP / PLM / CMMC L2)",
        "organization": "org-enterprise-it",
        "site_id": "site-mfg-01",
        "enclave_id": "enclave-cui-prod",
        "reporting_period": "2026-Q4",
        "workstreams": [
            {
                "workstream_id": "WS-01",
                "name": "IFS Cloud ERP Core & Shop-Floor Integration",
                "planned_value_usd": 1450000,
                "earned_value_usd": 1392000,
                "actual_cost_usd": 1365000,
                "cpi": 1.02,
                "spi": 0.96,
                "status": "AMBER",
                "owner_role": "TPM / Senior Systems Engineer",
            },
            {
                "workstream_id": "WS-02",
                "name": "Aras Innovator PLM & CUI Technical Data Package Vault",
                "planned_value_usd": 880000,
                "earned_value_usd": 897600,
                "actual_cost_usd": 855000,
                "cpi": 1.05,
                "spi": 1.02,
                "status": "GREEN",
                "owner_role": "TPM / Senior Systems Engineer",
            },
            {
                "workstream_id": "WS-03",
                "name": "CMMC Level 2 Enclave IaC & NIST 800-171 Hardening",
                "planned_value_usd": 620000,
                "earned_value_usd": 613800,
                "actual_cost_usd": 590000,
                "cpi": 1.04,
                "spi": 0.99,
                "status": "GREEN",
                "owner_role": "TPM / Senior Systems Engineer",
            },
            {
                "workstream_id": "WS-04",
                "name": "Identity (GCC High) & ServiceNow Orchestration Automation",
                "planned_value_usd": 410000,
                "earned_value_usd": 385400,
                "actual_cost_usd": 395000,
                "cpi": 0.98,
                "spi": 0.94,
                "status": "AMBER",
                "owner_role": "TPM / Senior Systems Engineer",
            },
        ],
        "raid_register": [
            {
                "id": "RISK-001",
                "type": "Risk",
                "severity": "HIGH",
                "title": "ServiceNow MID Server WinRM credential timeouts on 198.51.100.0/24 masking 22% of shop-floor CIs",
                "mitigation": "Deploy gMSA service principal via DSC and restrict port 5986 NSG rule to 198.51.100.25/32",
                "nist_control": "3.4.1 / 3.11.2",
                "target_closure_days": 14,
            },
            {
                "id": "ISSUE-002",
                "type": "Issue",
                "severity": "HIGH",
                "title": "3+ hop ticket ping-ponging between Corp-IT-Tier1, Enclave-SecOps, and Site-MFG-01-IT on GCC High MFA & ERP role requests",
                "mitigation": "Convert top 3 catalog items to pre-approved Standard Changes backed by PowerShell/Graph API orchestration",
                "nist_control": "3.1.1 / 3.1.5",
                "target_closure_days": 21,
            },
            {
                "id": "DEP-003",
                "type": "Dependency",
                "severity": "MEDIUM",
                "title": "Corporate Firewall Change Freeze window prior to IFS Cloud ERP production cutover",
                "mitigation": "Submit pre-validated Terraform NSG plan and automated OPA Security Dossier 15 days ahead of CAB",
                "nist_control": "3.13.1 / 3.4.3",
                "target_closure_days": 15,
            },
            {
                "id": "RISK-004",
                "type": "Risk",
                "severity": "MEDIUM",
                "title": "CLUS-VMW-MFG01-OT memory utilization at 88.5% ahead of MES collector deployment",
                "mitigation": "Rebalance non-CUI test workloads and decommission stale Windows Server 2016 CIs identified in Week-1 AD scan",
                "nist_control": "3.4.1 / 3.7.1",
                "target_closure_days": 30,
            },
        ],
        "cutover_readiness_checklist": [
            {
                "gate_id": "GATE-01",
                "category": "CMMC Level 2 / Security",
                "criterion": "100% of enclave endpoints enforce FIPS 140-2/3 & TLS 1.2/1.3 with >30 days cert validity",
                "nist_control": "3.13.8 / 3.13.11",
                "ready": True,
            },
            {
                "gate_id": "GATE-02",
                "category": "Infrastructure & Capacity",
                "category_detail": "enclave-cui-prod (192.0.2.0/24)",
                "criterion": "Hypervisor cluster compute/memory headroom >20% and immutable GeoRedundant backup verified",
                "nist_control": "3.8.9 / 3.4.1",
                "ready": True,
            },
            {
                "gate_id": "GATE-03",
                "category": "CMDB & Service Transition",
                "criterion": "MID Server discovery error rate <2% and all IFS Cloud / Aras PLM CIs mapped to upstream services",
                "nist_control": "3.4.1 / 3.12.3",
                "ready": False,
            },
            {
                "gate_id": "GATE-04",
                "category": "Identity & ITSM Runbooks",
                "criterion": "GCC High Conditional Access policy active and Site-MFG-01-IT Tier-2 runbooks signed off",
                "nist_control": "3.1.1 / 3.5.3",
                "ready": True,
            },
            {
                "gate_id": "GATE-05",
                "category": "FinOps & Program Controls",
                "criterion": "Infracost monthly cloud spend delta within approved $18,500 threshold and CPI >= 1.00",
                "nist_control": "PMI-EVM / FinOps",
                "ready": True,
            },
        ],
    }


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_all(output_dir: Path = RAW_DATA_DIR) -> Dict[str, Path]:
    """Generates all deterministic synthetic telemetry files and returns their paths."""
    rng = random.Random(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmdb_rows = generate_cmdb_inventory(rng, count=120)
    incident_rows = generate_incidents_90d(rng, cmdb_rows, count=450)
    sc_task_rows = generate_sc_tasks_90d(rng, count=300)
    change_rows = generate_change_requests_90d(rng, count=120)
    program_data = generate_program_governance_fixture()

    paths = {
        "cmdb": output_dir / "cmdb_ci_inventory.csv",
        "incidents": output_dir / "servicenow_incidents_90d.csv",
        "sc_tasks": output_dir / "servicenow_sc_tasks_90d.csv",
        "changes": output_dir / "servicenow_change_requests_90d.csv",
        "program": output_dir / "program_evm_raid_cutover.json",
    }

    _write_csv(paths["cmdb"], cmdb_rows)
    _write_csv(paths["incidents"], incident_rows)
    _write_csv(paths["sc_tasks"], sc_task_rows)
    _write_csv(paths["changes"], change_rows)
    paths["program"].write_text(json.dumps(program_data, indent=2), encoding="utf-8")

    return paths


if __name__ == "__main__":
    generated = generate_all()
    print("[OK] Generated deterministic Week-1 synthetic telemetry fixtures:")
    for key, file_path in generated.items():
        print(f"  - {key:<10}: {file_path}")
