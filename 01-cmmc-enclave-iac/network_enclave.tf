# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/network_enclave.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.1.20 (External Connections), 3.13.1 (Boundary Protection),
#                  3.13.6 (Network Communication by Exception / Default Deny)
# ITIL 4 / PMI:    ITIL 4 Infrastructure & Platform Mgmt |
#                  PMI Technical Boundary & Cutover Network Readiness
# ==============================================================================

resource "azurerm_virtual_network" "enclave_vnet" {
  name                = "vnet-${var.enclave_id}-${var.manufacturing_site_id}"
  location            = azurerm_resource_group.enclave_rg.location
  resource_group_name = azurerm_resource_group.enclave_rg.name
  address_space = [
    var.enclave_cui_subnet_cidr,
    var.site_mfg_dmz_subnet_cidr,
    var.corp_transit_subnet_cidr
  ]
  dns_servers = ["192.0.2.10", "192.0.2.11"]
  tags        = local.mandatory_tags
}

resource "azurerm_subnet" "cui_workload_subnet" {
  name                              = "snet-${var.enclave_id}-workloads"
  resource_group_name               = azurerm_resource_group.enclave_rg.name
  virtual_network_name              = azurerm_virtual_network.enclave_vnet.name
  address_prefixes                  = [var.enclave_cui_subnet_cidr]
  private_endpoint_network_policies = "Enabled"
}

resource "azurerm_subnet" "mfg_dmz_subnet" {
  name                              = "snet-${var.manufacturing_site_id}-ot-dmz"
  resource_group_name               = azurerm_resource_group.enclave_rg.name
  virtual_network_name              = azurerm_virtual_network.enclave_vnet.name
  address_prefixes                  = [var.site_mfg_dmz_subnet_cidr]
  private_endpoint_network_policies = "Enabled"
}

resource "azurerm_network_security_group" "cui_enclave_nsg" {
  name                = "nsg-${var.enclave_id}-zero-trust"
  location            = azurerm_resource_group.enclave_rg.location
  resource_group_name = azurerm_resource_group.enclave_rg.name
  tags                = local.mandatory_tags

  # Allow TLS 1.2/1.3 HTTPS ERP/PLM traffic strictly from Manufacturing Site DMZ
  security_rule {
    name                       = "Allow-HTTPS-From-Site-MFG-DMZ"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = var.site_mfg_dmz_subnet_cidr
    destination_address_prefix = var.enclave_cui_subnet_cidr
  }

  # Allow ServiceNow MID Server WinRM-HTTPS (5986) discovery strictly from MID host IP
  security_rule {
    name                       = "Allow-MID-Server-Discovery-WinRM-HTTPS"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5986"
    source_address_prefix      = "198.51.100.25/32"
    destination_address_prefix = var.enclave_cui_subnet_cidr
  }

  # Default Deny All Other Inbound Traffic (NIST SP 800-171 3.13.6)
  security_rule {
    name                       = "Deny-All-Inbound-Default"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "cui_nsg_assoc" {
  subnet_id                 = azurerm_subnet.cui_workload_subnet.id
  network_security_group_id = azurerm_network_security_group.cui_enclave_nsg.id
}
