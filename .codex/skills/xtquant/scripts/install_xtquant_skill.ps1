param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Target
)

$ErrorActionPreference = "Stop"

$resolvedSource = (Resolve-Path -LiteralPath $Source).Path
if (-not (Test-Path -LiteralPath $resolvedSource -PathType Container)) {
    throw "Source skill directory does not exist: $Source"
}

$resolvedTarget = [System.IO.Path]::GetFullPath($Target)
$targetParent = Split-Path -Parent $resolvedTarget
if (-not $targetParent) {
    throw "Target path must include a parent directory: $Target"
}

New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

if (Test-Path -LiteralPath $resolvedTarget) {
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}

Copy-Item -LiteralPath $resolvedSource -Destination $resolvedTarget -Recurse -Force

Write-Host "Installed xtquant skill."
Write-Host "Source: $resolvedSource"
Write-Host "Target: $resolvedTarget"
