# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/main.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.3.1 (Audit Logging), 3.3.2 (User Traceability),
#                  3.4.1 (System Inventory & CMDB Baseline)
# ITIL 4 / PMI:    ITIL 4 Information Security Mgmt & Asset Mgmt |
#                  PMI Cost/FinOps Accountability & Audit Readiness
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }
  }
}

provider "azurerm" {
  environment = var.cloud_environment
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

locals {
  mandatory_tags = {
    Organization       = var.enterprise_org_id
    EnclaveBoundary    = var.enclave_id
    ManufacturingSite  = var.manufacturing_site_id
    DomainNamespace    = var.domain_fqdn
    ComplianceStandard = "NIST-SP-800-171-Rev2-CMMC-L2"
    DataClassification = "CUI-Specified"
    ManagedBy          = "Terraform-IaC"
    CostCenter         = "CC-MFG-TRANSFORMATION-01"
  }
}

resource "azurerm_resource_group" "enclave_rg" {
  name     = "rg-${var.enclave_id}-${var.manufacturing_site_id}"
  location = "usgovvirginia"
  tags     = local.mandatory_tags
}

resource "azurerm_log_analytics_workspace" "enclave_siem" {
  name                       = "law-${var.enclave_id}-audit"
  location                   = azurerm_resource_group.enclave_rg.location
  resource_group_name        = azurerm_resource_group.enclave_rg.name
  sku                        = "PerGB2018"
  retention_in_days          = var.log_retention_days
  internet_ingestion_enabled = false
  internet_query_enabled     = false
  tags                       = local.mandatory_tags
}

resource "azurerm_recovery_services_vault" "enclave_backup_vault" {
  name                          = "rsv-${var.enclave_id}-dr"
  location                      = azurerm_resource_group.enclave_rg.location
  resource_group_name           = azurerm_resource_group.enclave_rg.name
  sku                           = "Standard"
  soft_delete_enabled           = true
  immutability                  = "Locked"
  public_network_access_enabled = false
  storage_mode_type             = "GeoRedundant"
  tags                          = local.mandatory_tags
}
