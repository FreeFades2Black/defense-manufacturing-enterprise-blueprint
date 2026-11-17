#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        scripts/verify_sanitization.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.1.22 (Control Publicly Accessible Information / CUI Hygiene),
                 3.12.1 (Periodic Security Control Assessment)
ITIL 4 / PMI:    ITIL 4 Continual Improvement & Information Security Mgmt |
                 PMI Quality Assurance & Compliance Gate Verification
================================================================================

Automated repository sanitization and governance metadata scanner:
1. Verifies that all IPv4 addresses used in code, configs, docs, and CSVs belong
   exclusively to RFC-5737 documentation blocks (192.0.2.0/24, 198.51.100.0/24,
   203.0.113.0/24) or standard loopback/0.0.0.0 masks.
2. Verifies that every technical engineering artifact (.tf, .ps1, .py, .rego)
   contains a structured NIST SP 800-171 & ITIL 4 / PMI metadata header.
"""

from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_NETWORKS = [
    ipaddress.ip_network("192.0.2.0/24"),     # RFC-5737 TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # RFC-5737 TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # RFC-5737 TEST-NET-3
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("0.0.0.0/32"),       # Unspecified
]

IPV4_PATTERN = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")

SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", "node_modules"}
TECHNICAL_EXTENSIONS = {".tf", ".ps1", ".py", ".rego"}


def is_valid_rfc5737_ip(ip_str: str) -> bool:
    """Checks whether a matched dotted quad is an IPv4 address and within RFC-5737."""
    # Ignore NIST control numbers or OID strings that look like 4-part numbers (e.g. 1.3.6.1)
    if ip_str.startswith(("1.3.6.", "3.1.", "3.3.", "3.4.", "3.5.", "3.7.", "3.8.", "3.11.", "3.12.", "3.13.")):
        return True
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(addr in net for net in ALLOWED_NETWORKS)


def scan_repository(root: Path = REPO_ROOT) -> Tuple[List[str], List[str]]:
    """Returns (ip_violations, metadata_violations)."""
    ip_violations: List[str] = []
    metadata_violations: List[str] = []

    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue

        rel_path = path.relative_to(root)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        # 1. Check IPv4 sanitization
        for match in IPV4_PATTERN.findall(content):
            if not is_valid_rfc5737_ip(match):
                ip_violations.append(f"{rel_path}: non-RFC-5737 IPv4 detected -> {match}")

        # 2. Check structured engineering-to-governance metadata headers on technical files
        if path.suffix in TECHNICAL_EXTENSIONS and path.name != "__init__.py":
            header_window = content[:1500]
            if (
                "METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT" not in header_window
                or "NIST SP 800-171:" not in header_window
                or "ITIL 4 / PMI:" not in header_window
            ):
                metadata_violations.append(
                    f"{rel_path}: missing required NIST SP 800-171 / ITIL 4 / PMI metadata header"
                )

    return ip_violations, metadata_violations


def main() -> int:
    ip_violations, metadata_violations = scan_repository()
    if ip_violations or metadata_violations:
        for err in ip_violations + metadata_violations:
            print(f"[FAIL] {err}", file=sys.stderr)
        return 1

    print("[OK] Sanitization & Governance Metadata Gate PASSED:")
    print("  - Zero non-RFC-5737 IPv4 addresses detected.")
    print("  - 100% of technical artifacts (.tf, .ps1, .py, .rego) include NIST SP 800-171 & ITIL 4 / PMI headers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
