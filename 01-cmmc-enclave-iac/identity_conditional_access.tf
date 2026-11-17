# ==============================================================================
# METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
# Artifact:        01-cmmc-enclave-iac/identity_conditional_access.tf
# Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
# NIST SP 800-171: 3.1.1 (Authorized Access), 3.1.5 (Least Privilege),
#                  3.1.11 (Session Lock/Termination), 3.5.3 (MFA for CUI Access)
# ITIL 4 / PMI:    ITIL 4 Access Management | PMI Identity & Governance Control
# ==============================================================================

resource "azuread_named_location" "trusted_enclave_egress" {
  display_name = "Trusted-Enclave-And-Site-MFG-01-Ranges"
  ip {
    ip_ranges = [
      var.enclave_cui_subnet_cidr,
      var.site_mfg_dmz_subnet_cidr
    ]
    trusted = true
  }
}

resource "azuread_conditional_access_policy" "cmmc_l2_enclave_zero_trust" {
  display_name = "CAP-001-Enclave-CUI-Prod-Phishing-Resistant-MFA"
  state        = "enabled"

  conditions {
    client_app_types = ["browser", "mobileAppsAndDesktopClients"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_users = ["All"]
    }

    locations {
      included_locations = ["All"]
      excluded_locations = [azuread_named_location.trusted_enclave_egress.id]
    }
  }

  grant_controls {
    operator                          = "AND"
    built_in_controls                 = ["mfa", "compliantDevice", "domainJoinedDevice"]
    authentication_strength_policy_id = "00000000-0000-0000-0000-000000000004" # Phishing-resistant MFA (FIDO2 / PIV)
  }

  session_controls {
    sign_in_frequency        = 8
    sign_in_frequency_period = "hours"
    persistent_browser_mode  = "never"
  }
}
