# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        03-policy-as-code-governance/policies/cmmc_enclave_guardrails.rego
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.3.1 (Audit Retention), 3.4.2 (Security Baseline),
#                  3.5.3 (MFA Enforcement), 3.13.1 (Boundary Protection),
#                  3.13.11 (FIPS Validated Cryptography)
# ITIL 4 / PMI:    ITIL 4 Change Enablement & InfoSec Mgmt |
#                  PMI Quality Gate & Automated POA&M Prevention
# ==============================================================================

package defense.mfg.cmmc_l2

import future.keywords.contains
import future.keywords.if
import future.keywords.in

mandatory_tags := {
    "Organization",
    "EnclaveBoundary",
    "ManufacturingSite",
    "ComplianceStandard",
    "CostCenter",
}

# NIST 3.3.1: Audit log retention must be >= 365 days
deny contains msg if {
    some rc in input.resource_changes
    rc.type == "azurerm_log_analytics_workspace"
    retention := rc.change.after.retention_in_days
    retention < 365
    msg := sprintf(
        "[NIST-3.3.1] Log Analytics Workspace '%s' retention (%d days) is below the 365-day CMMC Level 2 minimum.",
        [rc.name, retention]
    )
}

# NIST 3.13.11: Key Vault must use 'premium' SKU for FIPS 140-2/3 HSM backing and purge protection
deny contains msg if {
    some rc in input.resource_changes
    rc.type == "azurerm_key_vault"
     lower(rc.change.after.sku_name) != "premium"
    msg := sprintf(
        "[NIST-3.13.11] Key Vault '%s' must use 'premium' HSM SKU for FIPS 140-2/3 compliance.",
        [rc.name]
    )
}

deny contains msg if {
    some rc in input.resource_changes
    rc.type == "azurerm_key_vault"
    rc.change.after.purge_protection_enabled != true
    msg := sprintf(
        "[NIST-3.13.10] Key Vault '%s' must enable purge_protection_enabled = true.",
        [rc.name]
    )
}

# NIST 3.13.1 / 3.13.6: Prohibit wildcard inbound allow rules into enclave-cui-prod (192.0.2.0/24)
deny contains msg if {
    some rc in input.resource_changes
    rc.type == "azurerm_network_security_group"
    some rule in rc.change.after.security_rule
    rule.direction == "Inbound"
    rule.access == "Allow"
    rule.source_address_prefix in {"*", "0.0.0.0/0", "Internet"}
    msg := sprintf(
        "[NIST-3.13.1] NSG '%s' rule '%s' allows unrestricted inbound access from '%s'.",
        [rc.name, rule.name, rule.source_address_prefix]
    )
}

# NIST 3.4.1: Enforce mandatory CMDB & FinOps governance tags
deny contains msg if {
    some rc in input.resource_changes
    rc.change.after.tags != null
    provided_tags := {k | rc.change.after.tags[k]}
    missing := mandatory_tags - provided_tags
    count(missing) > 0
    msg := sprintf(
        "[NIST-3.4.1 / FinOps] Resource '%s' is missing mandatory governance tags: %v",
        [rc.address, missing]
    )
}
