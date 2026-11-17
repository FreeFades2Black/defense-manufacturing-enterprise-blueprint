#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        04-program-command-gateway/metrics_engine.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.4.1 (CMDB Baseline), 3.11.1 (Risk Register),
                 3.12.1 (Security Control Assessment), 3.12.3 (Monitoring)
ITIL 4 / PMI:    ITIL 4 Release Mgmt & Continual Improvement |
                 PMI Earned Value Management (CPI/SPI) & Cutover Governance
================================================================================

Data loader and Earned Value / Readiness aggregation engine backing the
Streamlit / Databricks App Transformation & Readiness Control Plane.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
GOLD_DIR = REPO_ROOT / "data" / "gold"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_module_from_path(module_name: str, file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_all_gold_artifacts() -> Dict[str, Any]:
    """Ensures raw synthetic telemetry and Gold layer artifacts exist and returns them."""
    if not (RAW_DIR / "program_evm_raid_cutover.json").exists():
        from scripts.generate_synthetic_telemetry import generate_all

        generate_all(RAW_DIR)

    if not (GOLD_DIR / "medallion_gold_summary.json").exists():
        pipeline_mod = _load_module_from_path(
            "medallion_pipeline",
            REPO_ROOT / "02-itsm-medallion-telemetry" / "pipeline.py",
        )
        pipeline_mod.run_medallion_pipeline(RAW_DIR, GOLD_DIR)

    if not (GOLD_DIR / "security_compliance_dossier.json").exists():
        dossier_mod = _load_module_from_path(
            "security_dossier",
            REPO_ROOT / "03-policy-as-code-governance" / "generate_security_dossier.py",
        )
        dossier_mod.generate_security_dossier(GOLD_DIR)

    if not (GOLD_DIR / "finops_infracost_gate.json").exists():
        finops_mod = _load_module_from_path(
            "finops_gate",
            REPO_ROOT / "03-policy-as-code-governance" / "evaluate_finops_gate.py",
        )
        finops_mod.evaluate_infracost_diff(gold_dir=GOLD_DIR)

    program_data = json.loads(
        (RAW_DIR / "program_evm_raid_cutover.json").read_text(encoding="utf-8")
    )
    medallion_summary = json.loads(
        (GOLD_DIR / "medallion_gold_summary.json").read_text(encoding="utf-8")
    )
    security_dossier = json.loads(
        (GOLD_DIR / "security_compliance_dossier.json").read_text(encoding="utf-8")
    )
    finops_gate = json.loads(
        (GOLD_DIR / "finops_infracost_gate.json").read_text(encoding="utf-8")
    )

    workstreams = program_data["workstreams"]
    total_pv = sum(w["planned_value_usd"] for w in workstreams)
    total_ev = sum(w["earned_value_usd"] for w in workstreams)
    total_ac = sum(w["actual_cost_usd"] for w in workstreams)
    portfolio_cpi = round(total_ev / total_ac, 2)
    portfolio_spi = round(total_ev / total_pv, 2)

    gates = program_data["cutover_readiness_checklist"]
    ready_gates = sum(1 for g in gates if g["ready"])

    return {
        "program": program_data,
        "portfolio_evm": {
            "total_pv_usd": total_pv,
            "total_ev_usd": total_ev,
            "total_ac_usd": total_ac,
            "portfolio_cpi": portfolio_cpi,
            "portfolio_spi": portfolio_spi,
            "cost_variance_usd": total_ev - total_ac,
            "schedule_variance_usd": total_ev - total_pv,
        },
        "cutover_summary": {
            "ready_gates": ready_gates,
            "total_gates": len(gates),
            "readiness_pct": round((ready_gates / len(gates)) * 100.0, 1),
            "overall_go_no_go": "CONDITIONAL_HOLD (Remediate GATE-03 MID Server CIs)"
            if ready_gates < len(gates)
            else "GO_FOR_CUTOVER",
        },
        "medallion": medallion_summary,
        "security_dossier": security_dossier,
        "finops_gate": finops_gate,
    }
