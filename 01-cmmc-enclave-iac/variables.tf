# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/variables.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.4.1 (Baseline Configuration), 3.4.2 (Security Settings)
# ITIL 4 / PMI:    ITIL 4 Service Configuration Mgmt | PMI Configuration Control
# ==============================================================================

variable "enterprise_org_id" {
  description = "Sanitized corporate IT organization identifier."
  type        = string
  default     = "org-enterprise-it"
}

variable "enclave_id" {
  description = "Sanitized CMMC Level 2 regulated CUI enclave identifier."
  type        = string
  default     = "enclave-cui-prod"
}

variable "manufacturing_site_id" {
  description = "Sanitized manufacturing facility identifier."
  type        = string
  default     = "site-mfg-01"
}

variable "domain_fqdn" {
  description = "Sanitized internal Active Directory / DNS domain namespace."
  type        = string
  default     = "example-mfg.local"
}

variable "cloud_environment" {
  description = "Target sovereign cloud boundary (usgovernment for Azure Gov / GCC High)."
  type        = string
  default     = "usgovernment"
}

variable "enclave_cui_subnet_cidr" {
  description = "RFC-5737 TEST-NET-1 CIDR allocated to the CUI production enclave."
  type        = string
  default     = "192.0.2.0/24"
}

variable "site_mfg_dmz_subnet_cidr" {
  description = "RFC-5737 TEST-NET-2 CIDR allocated to the Site Manufacturing OT/MES DMZ."
  type        = string
  default     = "198.51.100.0/24"
}

variable "corp_transit_subnet_cidr" {
  description = "RFC-5737 TEST-NET-3 CIDR allocated to Corporate IT transit and PAM boundary."
  type        = string
  default     = "203.0.113.0/24"
}

variable "log_retention_days" {
  description = "Audit log retention period in days (minimum 365 days for CMMC Level 2 / NIST 3.3.1)."
  type        = number
  default     = 365

  validation {
    condition     = var.log_retention_days >= 365
    error_message = "NIST SP 800-171 3.3.1 requires a minimum of 365 days of audit log retention."
  }
}

variable "monthly_budget_limit_usd" {
  description = "Approved monthly cloud infrastructure budget guardrail in USD for CPI/FinOps governance."
  type        = number
  default     = 18500
}
