$ErrorActionPreference = "Stop"

$scriptRoot = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.ScriptName }
$project = Join-Path $scriptRoot "JarvisMicRecorder\JarvisMicRecorder.csproj"

function Resolve-Dotnet {
    $command = Get-Command dotnet -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    $candidates = @(
        "C:\Program Files\dotnet\dotnet.exe",
        "C:\Program Files (x86)\dotnet\dotnet.exe",
        (Join-Path $env:LOCALAPPDATA "Microsoft\dotnet\dotnet.exe")
    )
    foreach ($candidate in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }
    throw "dotnet was not found. Install the .NET SDK or add dotnet.exe to PATH."
}

$dotnet = Resolve-Dotnet
& $dotnet restore $project
& $dotnet publish $project -c Release -r win-x64 --self-contained false

$exe = Join-Path $scriptRoot "JarvisMicRecorder\bin\Release\net10.0-windows\win-x64\publish\JarvisMicRecorder.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "publish completed but recorder exe was not found: $exe"
}

Write-Host "Jarvis mic recorder published:"
Write-Host $exe
