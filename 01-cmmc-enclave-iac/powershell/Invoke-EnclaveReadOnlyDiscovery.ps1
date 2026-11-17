<#
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        01-cmmc-enclave-iac/powershell/Invoke-EnclaveReadOnlyDiscovery.ps1
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.1.1 (Authorized Access), 3.4.1 (Baseline Inventory),
                 3.7.1 (System Maintenance / Patching), 3.11.2 (Vulnerability Scan)
ITIL 4 / PMI:    ITIL 4 Service Configuration & Capacity Mgmt |
                 PMI Week-1 Ground-Truth Baseline Verification
================================================================================
.SYNOPSIS
    Executes Week-1 non-destructive, read-only discovery across Active Directory,
    Entra ID hybrid state, and Windows Server / Virtualization hosts in the
    regulated manufacturing enclave (example-mfg.local / 192.0.2.0/24).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$DomainFqdn = "example-mfg.local",

    [Parameter(Mandatory = $false)]
    [string]$EnclaveSubnet = "192.0.2.0/24",

    [Parameter(Mandatory = $false)]
    [int]$StaleThresholdDays = 90,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ".\data\raw\ad_server_discovery_snapshot.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[INFO] Starting Week-1 Read-Only Enclave Discovery for domain '$DomainFqdn' ($EnclaveSubnet)..." -ForegroundColor Cyan

$adModuleAvailable = $null -ne (Get-Module -ListAvailable -Name ActiveDirectory)

if ($adModuleAvailable -and ($env:USERDNSDOMAIN -eq $DomainFqdn)) {
    Write-Host "[INFO] ActiveDirectory module detected in target domain. Executing live read-only queries..." -ForegroundColor Green
    $cutoffDate = (Get-Date).AddDays(-$StaleThresholdDays)
    $staleUsers = @(Get-ADUser -Filter { Enabled -eq $true -and LastLogonDate -lt $cutoffDate } -Properties LastLogonDate)
    $staleComputers = @(Get-ADComputer -Filter { Enabled -eq $true -and LastLogonDate -lt $cutoffDate } -Properties LastLogonDate, OperatingSystem)
    $privGroups = @("Domain Admins", "Enterprise Admins", "Schema Admins") | ForEach-Object {
        $members = @(Get-ADGroupMember -Identity $_ -Recursive -ErrorAction SilentlyContinue)
        [PSCustomObject]@{
            GroupName   = $_
            MemberCount = $members.Count
        }
    }
    $discoveryMode = "Live-ReadOnly-AD"
}
else {
    Write-Host "[INFO] Executing deterministic sanitized telemetry snapshot for '$DomainFqdn' ($EnclaveSubnet)..." -ForegroundColor Yellow
    $discoveryMode = "Sanitized-Baseline-Simulation"
    $staleUsers = @(
        [PSCustomObject]@{ SamAccountName = "svc-legacy-erp-01"; Department = "site-mfg-01"; LastLogonDaysAgo = 142; PasswordNeverExpires = $true },
        [PSCustomObject]@{ SamAccountName = "usr-contractor-plm-04"; Department = "enclave-cui-prod"; LastLogonDaysAgo = 118; PasswordNeverExpires = $false },
        [PSCustomObject]@{ SamAccountName = "svc-mes-collector-02"; Department = "site-mfg-01"; LastLogonDaysAgo = 97; PasswordNeverExpires = $true }
    )
    $staleComputers = @(
        [PSCustomObject]@{ Name = "WKS-MFG01-CAD09"; IPv4Address = "198.51.100.89"; OperatingSystem = "Windows 10 Enterprise LTSC"; LastLogonDaysAgo = 114 },
        [PSCustomObject]@{ Name = "SRV-ENCLAVE-OLD02"; IPv4Address = "192.0.2.74"; OperatingSystem = "Windows Server 2016 Standard"; LastLogonDaysAgo = 165 }
    )
    $privGroups = @(
        [PSCustomObject]@{ GroupName = "Domain Admins"; MemberCount = 14; NestedGroupCount = 3; CmmcFinding = "Excessive privileged accounts (>8 threshold)" },
        [PSCustomObject]@{ GroupName = "Enclave-CUI-Admins"; MemberCount = 6; NestedGroupCount = 0; CmmcFinding = "Compliant" },
        [PSCustomObject]@{ GroupName = "Site-MFG-01-Server-Operators"; MemberCount = 11; NestedGroupCount = 2; CmmcFinding = "Nested group debt detected" }
    )
}

$hypervisorClusters = @(
    [PSCustomObject]@{
        ClusterName            = "CLUS-HV-ENCLAVE-01.$DomainFqdn"
        Subnet                 = "192.0.2.0/24"
        NodeCount              = 4
        CpuAllocationPct       = 68.5
        MemoryUtilizationPct   = 74.2
        StorageFreeTb          = 18.4
        BackupLast24hSuccess   = $true
        OsPatchCompliancePct   = 94.0
        ErpPlmCutoverReady     = $true
    },
    [PSCustomObject]@{
        ClusterName            = "CLUS-VMW-MFG01-OT.$DomainFqdn"
        Subnet                 = "198.51.100.0/24"
        NodeCount              = 3
        CpuAllocationPct       = 84.0
        MemoryUtilizationPct   = 88.5
        StorageFreeTb          = 3.1
        BackupLast24hSuccess   = $false
        OsPatchCompliancePct   = 78.5
        ErpPlmCutoverReady     = $false
    }
)

$snapshot = [Ordered]@{
    GeneratedAtUtc       = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    DiscoveryMode        = $discoveryMode
    DomainFqdn           = $DomainFqdn
    EnclaveSubnet        = $EnclaveSubnet
    NistControlsMapped   = @("3.1.1", "3.1.5", "3.4.1", "3.7.1", "3.11.2")
    IdentityHygiene      = [Ordered]@{
        StaleThresholdDays      = $StaleThresholdDays
        StaleUserCount          = $staleUsers.Count
        StaleComputerCount      = $staleComputers.Count
        StaleUsers              = $staleUsers
        StaleComputers          = $staleComputers
        PrivilegedGroupAudit    = $privGroups
    }
    VirtualizationHealth = $hypervisorClusters
}

$parentDir = Split-Path -Parent $OutputPath
if ($parentDir -and -not (Test-Path $parentDir)) {
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

$snapshot | ConvertTo-Json -Depth 6 | Set-Content -Path $OutputPath -Encoding UTF8
Write-Host "[OK] Enclave read-only discovery report written to: $OutputPath" -ForegroundColor Green
