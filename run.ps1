param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvDir = Join-Path $scriptDir ".venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$readyMarker = Join-Path $venvDir ".pcswmm-v0.1-ready"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Creating local Python environment..." -ForegroundColor Cyan

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvDir
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvDir
    }
    else {
        throw "Python 3 was not found. Install Python 3, then run this script again."
    }
}

if (-not $SkipInstall -and -not (Test-Path $readyMarker)) {
    Write-Host "Installing PCSWMM Data Extractor dependencies..." -ForegroundColor Cyan
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r (Join-Path $scriptDir "requirements.txt")
    New-Item -ItemType File -Path $readyMarker -Force | Out-Null
}

$env:PYTHONUTF8 = "1"
Write-Host "Launching PCSWMM Data Extractor v0.1..." -ForegroundColor Green
& $pythonExe (Join-Path $scriptDir "pcswmm_data_extractor.py")
