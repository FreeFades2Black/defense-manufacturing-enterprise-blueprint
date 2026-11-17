# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/outputs.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.4.1 (Baseline Inventory), 3.12.4 (SSP Architecture Output)
# ITIL 4 / PMI:    ITIL 4 Service Configuration Mgmt | PMI Deliverable Handoff
# ==============================================================================

output "enclave_resource_group_name" {
  description = "Provisioned Resource Group for the CMMC Level 2 Enclave."
  value       = azurerm_resource_group.enclave_rg.name
}

output "enclave_siem_workspace_id" {
  description = "Log Analytics Workspace ID enforcing 365-day NIST 3.3.1 retention."
  value       = azurerm_log_analytics_workspace.enclave_siem.id
}

output "enclave_cui_subnet_id" {
  description = "Subnet ID for regulated CUI workloads (192.0.2.0/24)."
  value       = azurerm_subnet.cui_workload_subnet.id
}

output "fips_key_vault_uri" {
  description = "FIPS 140-2/3 HSM-backed Key Vault URI for ERP/PLM TLS lifecycle."
  value       = azurerm_key_vault.enclave_fips_kv.vault_uri
}
