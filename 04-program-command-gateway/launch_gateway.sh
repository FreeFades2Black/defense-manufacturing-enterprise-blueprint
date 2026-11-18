#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

python3 scripts/generate_synthetic_telemetry.py
python3 02-itsm-medallion-telemetry/pipeline.py --source synthetic
python3 03-policy-as-code-governance/generate_security_dossier.py
python3 03-policy-as-code-governance/evaluate_finops_gate.py

exec python3 -m streamlit run 04-program-command-gateway/app.py --server.port 8501 --server.headless true
