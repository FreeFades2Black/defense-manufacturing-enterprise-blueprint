#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        tests/test_enterprise_blueprint.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.12.1 (Periodic Security Control Assessment),
                 3.12.3 (Continuous Monitoring), 3.4.1 (Baseline Verification)
ITIL 4 / PMI:    ITIL 4 Service Validation & Testing |
                 PMI Quality Assurance & Empirical Baseline Verification
================================================================================

End-to-end test suite verifying:
1. Strict RFC-5737 IPv4 sanitization and NIST SP 800-171 / ITIL 4 / PMI headers.
2. Deterministic 90-day ServiceNow & CMDB synthetic fixture generation.
3. Medallion Lakehouse Bronze -> Silver -> Gold transformations & Pareto metrics.
4. Automated CMMC Level 2 Security Dossier and FinOps Infracost budget gates.
5. Transformation & Readiness Control Plane EVM (CPI/SPI) & Cutover calculations.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str) -> Any:
    full_path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, full_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sanitization_and_governance_headers() -> None:
    verifier = _load_module("verify_sanitization", "scripts/verify_sanitization.py")
    ip_violations, metadata_violations = verifier.scan_repository(REPO_ROOT)
    assert ip_violations == [], f"Found non-RFC-5737 IPs: {ip_violations}"
    assert metadata_violations == [], f"Missing governance headers: {metadata_violations}"


def test_synthetic_telemetry_generation() -> None:
    gen = _load_module("generate_synthetic_telemetry", "scripts/generate_synthetic_telemetry.py")
    paths = gen.generate_all()
    for key, path in paths.items():
        assert path.exists(), f"Expected generated fixture for {key} at {path}"
        assert path.stat().st_size > 100


def test_medallion_lakehouse_pipeline() -> None:
    pipeline = _load_module("medallion_pipeline", "02-itsm-medallion-telemetry/pipeline.py")
    summary = pipeline.run_medallion_pipeline()

    assert summary["scope"]["site_id"] == "site-mfg-01"
    assert summary["scope"]["enclave_id"] == "enclave-cui-prod"
    assert summary["incident_kpis"]["total_incidents_90d"] == 450
    assert summary["incident_kpis"]["ping_pong_rate_pct"] > 30.0
    assert summary["cmdb_and_mid_kpis"]["total_server_cis"] == 120
    assert summary["cmdb_and_mid_kpis"]["orphan_ci_count"] > 0

    top_driver = summary["top_pareto_bottlenecks"][0]
    assert top_driver["subcategory"] in {
        "GCC-High-MFA-Provisioning",
        "IFS-ERP-Role-Entitlement",
    }


def test_cmmc_security_dossier_and_finops_gate() -> None:
    dossier_mod = _load_module(
        "generate_security_dossier",
        "03-policy-as-code-governance/generate_security_dossier.py",
    )
    dossier = dossier_mod.generate_security_dossier()
    assert dossier["gate_status"] == "PASSED"
    assert dossier["compliance_score_pct"] == 100.0
    assert (REPO_ROOT / "data" / "gold" / "SECURITY_COMPLIANCE_DOSSIER.md").exists()

    finops_mod = _load_module(
        "evaluate_finops_gate",
        "03-policy-as-code-governance/evaluate_finops_gate.py",
    )
    finops = finops_mod.evaluate_infracost_diff()
    assert finops["finops_gate_status"] == "PASSED"
    assert finops["proposed_monthly_cost_usd"] <= finops["approved_monthly_budget_usd"]


def test_program_command_gateway_metrics_engine() -> None:
    engine = _load_module("metrics_engine", "04-program-command-gateway/metrics_engine.py")
    state = engine.ensure_all_gold_artifacts()

    assert state["portfolio_evm"]["portfolio_cpi"] >= 1.00
    assert 0.90 <= state["portfolio_evm"]["portfolio_spi"] <= 1.10
    assert state["cutover_summary"]["total_gates"] == 5
    assert len(state["program"]["raid_register"]) == 4
