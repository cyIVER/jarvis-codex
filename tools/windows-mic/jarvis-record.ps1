param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AdapterArgs
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message, [int]$Code = 2) {
    [Console]::Error.WriteLine($Message)
    exit $Code
}

function Read-Value([string[]]$Tokens, [ref]$Index, [string]$Name) {
    if (($Index.Value + 1) -ge $Tokens.Count -or $Tokens[$Index.Value + 1].StartsWith("--")) {
        Fail "$Name requires a value"
    }
    $Index.Value++
    return $Tokens[$Index.Value]
}

function Convert-OutputPath([string]$PathValue) {
    if ($PathValue -match '^/[A-Za-z0-9_./-]+') {
        $converted = & wsl.exe wslpath -w -- "$PathValue"
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($converted)) {
            Fail "failed to convert WSL output path: $PathValue" 1
        }
        return $converted.Trim()
    }
    return $PathValue
}

function Resolve-RecorderExe() {
    if (-not [string]::IsNullOrWhiteSpace($env:JARVIS_MIC_RECORDER_EXE)) {
        return $env:JARVIS_MIC_RECORDER_EXE
    }

    $scriptRoot = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.ScriptName }
    $candidates = @(
        (Join-Path $scriptRoot "JarvisMicRecorder\bin\Release\net10.0-windows\win-x64\publish\JarvisMicRecorder.exe"),
        (Join-Path $scriptRoot "JarvisMicRecorder\bin\Release\net10.0-windows\win-x64\JarvisMicRecorder.exe"),
        (Join-Path $scriptRoot "JarvisMicRecorder\bin\Debug\net10.0-windows\win-x64\JarvisMicRecorder.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    Fail "JarvisMicRecorder.exe was not found. Run tools/windows-mic/build.ps1 or set JARVIS_MIC_RECORDER_EXE." 1
}

$outputFile = $null
$seconds = $null
$deviceIndex = $null

for ($i = 0; $i -lt $AdapterArgs.Count; $i++) {
    switch ($AdapterArgs[$i]) {
        "--output-file" {
            $outputFile = Read-Value -Tokens $AdapterArgs -Index ([ref]$i) -Name "--output-file"
        }
        "--seconds" {
            $seconds = Read-Value -Tokens $AdapterArgs -Index ([ref]$i) -Name "--seconds"
        }
        "--device-index" {
            $deviceIndex = Read-Value -Tokens $AdapterArgs -Index ([ref]$i) -Name "--device-index"
        }
        default {
            Fail "unknown recorder adapter argument: $($AdapterArgs[$i])"
        }
    }
}

if ([string]::IsNullOrWhiteSpace($outputFile)) {
    Fail "--output-file is required"
}
if ([string]::IsNullOrWhiteSpace($seconds)) {
    Fail "--seconds is required"
}

$recorder = Resolve-RecorderExe
$windowsOutput = Convert-OutputPath $outputFile
$recorderArgs = @("--output-file", $windowsOutput, "--seconds", $seconds)
if (-not [string]::IsNullOrWhiteSpace($deviceIndex)) {
    $recorderArgs += @("--device-index", $deviceIndex)
}

& $recorder @recorderArgs
exit $LASTEXITCODE
