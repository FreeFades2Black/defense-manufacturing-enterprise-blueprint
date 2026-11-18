# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        Makefile
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.4.2 (Automated Baseline Execution), 3.12.1 (Continuous Audit)
# ITIL 4 / PMI:    ITIL 4 Release & Deployment Mgmt | PMI Reproducible Gate DX
# ==============================================================================

PYTHON ?= python3
SOURCE ?= synthetic

.PHONY: help bootstrap pipeline audit gateway clean

help: ## Display available single-command operational targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Install dependencies and generate 90-day synthetic ServiceNow & CMDB telemetry
	$(PYTHON) -m pip install --quiet -r requirements.txt
	$(PYTHON) scripts/generate_synthetic_telemetry.py

pipeline: ## Run Module 02 Medallion Lakehouse (--source $(SOURCE)) and Module 03 Security Dossier & FinOps gates
	$(PYTHON) 02-itsm-medallion-telemetry/pipeline.py --source $(SOURCE)
	$(PYTHON) 03-policy-as-code-governance/generate_security_dossier.py
	$(PYTHON) 03-policy-as-code-governance/evaluate_finops_gate.py

audit: ## Execute RFC-5737 sanitization check, Python syntax/lint verification, and pytest suite
	$(PYTHON) scripts/verify_sanitization.py
	$(PYTHON) -m py_compile scripts/*.py 02-itsm-medallion-telemetry/*.py 03-policy-as-code-governance/*.py 04-program-command-gateway/*.py tests/*.py
	@if command -v ruff >/dev/null 2>&1; then ruff check .; fi
	@if command -v tflint >/dev/null 2>&1; then tflint --chdir=01-cmmc-enclave-iac; fi
	$(PYTHON) -m pytest -v

gateway: ## Launch Module 04 Streamlit Transformation & Readiness Command Gateway
	$(PYTHON) -m streamlit run 04-program-command-gateway/app.py --server.port 8501

clean: ## Remove local Python and pytest caches
	rm -rf .pytest_cache __pycache__ */__pycache__
