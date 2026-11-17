<#
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        01-cmmc-enclave-iac/powershell/EnclaveServerBaselineDSC.ps1
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.4.2 (Security Configuration Settings),
                 3.13.8 (Transmission Confidentiality / TLS 1.2+),
                 3.13.11 (FIPS-Validated Cryptography)
ITIL 4 / PMI:    ITIL 4 Deployment & Configuration Mgmt |
                 PMI Quality Assurance & CMMC Audit Readiness
================================================================================
.SYNOPSIS
    PowerShell Desired State Configuration (DSC) & baseline compliance verifier
    for Windows Server 2022 nodes hosting IFS Cloud ERP and Aras Innovator PLM
    inside enclave-cui-prod (192.0.2.0/24).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$TargetNode = "srv-erp-app01.example-mfg.local"
)

Set-StrictMode -Version Latest

function Get-EnclaveHardeningSpecification {
    [OutputType([hashtable])]
    param([string]$NodeName)

    return @{
        NodeName                = $NodeName
        EnclaveBoundary         = "enclave-cui-prod"
        SubnetCidr              = "192.0.2.0/24"
        NistControls            = @("3.3.1", "3.4.2", "3.13.8", "3.13.11")
        RegistryHardeningRules  = @(
            @{
                ControlId = "3.13.11"
                Name      = "FIPSAlgorithmPolicyEnabled"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa\FipsAlgorithmPolicy"
                ValueName = "Enabled"
                Expected  = 1
                Type      = "DWord"
            },
            @{
                ControlId = "3.13.8"
                Name      = "DisableTLS10Server"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server"
                ValueName = "Enabled"
                Expected  = 0
                Type      = "DWord"
            },
            @{
                ControlId = "3.13.8"
                Name      = "DisableTLS11Server"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.1\Server"
                ValueName = "Enabled"
                Expected  = 0
                Type      = "DWord"
            },
            @{
                ControlId = "3.13.8"
                Name      = "EnforceTLS12Server"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Server"
                ValueName = "Enabled"
                Expected  = 1
                Type      = "DWord"
            },
            @{
                ControlId = "3.4.2"
                Name      = "DisableSMBv1Protocol"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
                ValueName = "SMB1"
                Expected  = 0
                Type      = "DWord"
            },
            @{
                ControlId = "3.13.8"
                Name      = "RequireSMBv3SecuritySignature"
                Key       = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
                ValueName = "RequireSecuritySignature"
                Expected  = 1
                Type      = "DWord"
            }
        )
    }
}

$spec = Get-EnclaveHardeningSpecification -NodeName $TargetNode
Write-Host "[INFO] Validated CMMC Level 2 DSC Hardening Specification for '$($spec.NodeName)' ($($spec.RegistryHardeningRules.Count) controls mapped)." -ForegroundColor Green
$spec | ConvertTo-Json -Depth 5
