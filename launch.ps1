param(
    [ValidateSet('gui', 'check', 'smoke')]
    [string]$Mode = 'gui'
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/isaacsim.exe')) {
        throw 'Isaac Sim is not installed. Run setup.ps1 first.'
    }
    switch ($Mode) {
        'gui' { & ./.venv/Scripts/isaacsim.exe isaacsim.exp.full --/telemetry/enableAnonymousAppName=false --/telemetry/enableAnonymousData=false }
        'check' { & ./.venv/Scripts/isaacsim.exe isaacsim.exp.compatibility_check --/telemetry/enableAnonymousAppName=false --/telemetry/enableAnonymousData=false }
        'smoke' { & ./.venv/Scripts/python.exe scripts/smoke_test.py }
    }
    if ($LASTEXITCODE -ne 0) { throw "Isaac Sim exited with code $LASTEXITCODE." }
} finally {
    Pop-Location
}
