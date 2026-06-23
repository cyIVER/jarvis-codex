param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $JarvisArgs
)

$ErrorActionPreference = "Stop"

$repo = if ($env:JARVIS_WSL_REPO) { $env:JARVIS_WSL_REPO } else { "/home/iveri/repos/jarvis-codex" }
$distroArgs = @()
if ($env:JARVIS_WSL_DISTRO) {
    $distroArgs = @("-d", $env:JARVIS_WSL_DISTRO)
}

$escapedArgs = @()
foreach ($arg in $JarvisArgs) {
    $escapedArgs += "'" + ($arg -replace "'", "'\''") + "'"
}
$argText = $escapedArgs -join " "
$command = "command -v jarvis >/dev/null 2>&1 && exec jarvis $argText || exec uv run jarvis $argText"

& wsl.exe @distroArgs --cd $repo -- bash -lc $command
exit $LASTEXITCODE
