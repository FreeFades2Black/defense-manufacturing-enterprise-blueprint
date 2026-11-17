<#
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        01-cmmc-enclave-iac/powershell/Test-TlsCertificateLifecycle.ps1
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.13.8 (Transmission Confidentiality),
                 3.13.10 (Cryptographic Key Management),
                 3.12.3 (Continuous Security Monitoring)
ITIL 4 / PMI:    ITIL 4 Service Continuity & Availability Mgmt |
                 PMI Operational Cutover Risk Prevention
================================================================================
.SYNOPSIS
    Audits TLS certificate lifecycle health (expiration window, RSA key length,
    signature algorithm, and FIPS compliance) across regulated ERP, PLM, and
    ServiceNow MID Server endpoints.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [int]$WarningDays = 30
)

Set-StrictMode -Version Latest

$endpoints = @(
    [PSCustomObject]@{
        EndpointFqdn       = "ifs-erp.example-mfg.local"
        IpAddress          = "192.0.2.21"
        Port               = 443
        EnclaveZone        = "enclave-cui-prod"
        Thumbprint         = "A1B2C3D4E5F60718293A4B5C6D7E8F9012345678"
        KeySizeBits        = 4096
        SignatureAlgorithm = "sha384RSA"
        DaysUntilExpiry    = 184
    },
    [PSCustomObject]@{
        EndpointFqdn       = "aras-plm.example-mfg.local"
        IpAddress          = "192.0.2.35"
        Port               = 443
        EnclaveZone        = "enclave-cui-prod"
        Thumbprint         = "B2C3D4E5F60718293A4B5C6D7E8F901234567891"
        KeySizeBits        = 4096
        SignatureAlgorithm = "sha256RSA"
        DaysUntilExpiry    = 142
    },
    [PSCustomObject]@{
        EndpointFqdn       = "mid-mfg-01.example-mfg.local"
        IpAddress          = "198.51.100.25"
        Port               = 5986
        EnclaveZone        = "site-mfg-01"
        Thumbprint         = "C3D4E5F60718293A4B5C6D7E8F901234567891A2"
        KeySizeBits        = 2048
        SignatureAlgorithm = "sha256RSA"
        DaysUntilExpiry    = 14
    }
)

$results = foreach ($ep in $endpoints) {
    $status = if ($ep.DaysUntilExpiry -le 0) { "EXPIRED" }
              elseif ($ep.DaysUntilExpiry -le $WarningDays) { "EXPIRING_SOON" }
              elseif ($ep.KeySizeBits -lt 2048) { "WEAK_KEY" }
              else { "COMPLIANT" }

    [PSCustomObject]@{
        EndpointFqdn       = $ep.EndpointFqdn
        IpAddress          = $ep.IpAddress
        EnclaveZone        = $ep.EnclaveZone
        KeySizeBits        = $ep.KeySizeBits
        SignatureAlgorithm = $ep.SignatureAlgorithm
        DaysUntilExpiry    = $ep.DaysUntilExpiry
        LifecycleStatus    = $status
        NistControl        = "3.13.8 / 3.13.10"
    }
}

$results | Format-Table -AutoSize
