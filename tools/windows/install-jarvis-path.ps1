param(
    [string] $LauncherDirectory = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$resolved = (Resolve-Path -LiteralPath $LauncherDirectory).Path
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$entries = @()
if ($userPath) {
    $entries = $userPath -split ";" | Where-Object { $_ -ne "" }
}

$alreadyPresent = $false
foreach ($entry in $entries) {
    if ([string]::Equals($entry.TrimEnd([char]92), $resolved.TrimEnd([char]92), [StringComparison]::OrdinalIgnoreCase)) {
        $alreadyPresent = $true
        break
    }
}

if (-not $alreadyPresent) {
    $newPath = if ($userPath) { "$userPath;$resolved" } else { $resolved }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

[PSCustomObject]@{
    Status = if ($alreadyPresent) { "already-present" } else { "installed" }
    LauncherDirectory = $resolved
    Command = "jarvis"
    Note = "Open a new PowerShell window before relying on the updated user PATH."
} | ConvertTo-Json -Depth 3
