# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/keyvault_tls.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.13.8 (Transmission Confidentiality),
#                  3.13.10 (Cryptographic Key Management),
#                  3.13.11 (FIPS-Validated Cryptography)
# ITIL 4 / PMI:    ITIL 4 Service Continuity & Security Mgmt |
#                  PMI Technical Risk Prevention (Zero Certificate Outages)
# ==============================================================================

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "enclave_fips_kv" {
  name                          = "kv-enclave-cui-prod-01"
  location                      = azurerm_resource_group.enclave_rg.location
  resource_group_name           = azurerm_resource_group.enclave_rg.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "premium" # Premium SKU enforces FIPS 140-2/3 HSM backing
  enable_rbac_authorization     = true
  purge_protection_enabled      = true
  soft_delete_retention_days    = 90
  public_network_access_enabled = false

  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    ip_rules                   = [var.enclave_cui_subnet_cidr]
    virtual_network_subnet_ids = [azurerm_subnet.cui_workload_subnet.id]
  }

  tags = local.mandatory_tags
}

resource "azurerm_key_vault_certificate" "erp_plm_gateway_tls" {
  name         = "cert-erp-plm-enclave-gateway"
  key_vault_id = azurerm_key_vault.enclave_fips_kv.id

  certificate_policy {
    issuer_parameters {
      name = "Self"
    }

    key_properties {
      exportable = false
      key_size   = 4096
      key_type   = "RSA-HSM"
      reuse_key  = false
    }

    lifetime_action {
      action {
        action_type = "AutoRenew"
      }
      trigger {
        days_before_expiry = 30
      }
    }

    secret_properties {
      content_type = "application/x-pkcs12"
    }

    x509_certificate_properties {
      extended_key_usage = ["1.3.6.1.5.5.7.3.1"]
      key_usage = [
        "digitalSignature",
        "keyEncipherment",
      ]
      subject            = "CN=erp-gateway.${var.domain_fqdn}"
      validity_in_months = 12

      subject_alternative_names {
        dns_names = [
          "ifs-erp.${var.domain_fqdn}",
          "aras-plm.${var.domain_fqdn}",
          "mid-mfg-01.${var.domain_fqdn}"
        ]
      }
    }
  }
}
