# ClaimPilot - Run Script
param(
    [ValidateSet("backend", "frontend", "all", "mock-data", "test")]
    [string]$Target = "all"
)

$ROOT_DIR = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Generate-MockData {
    Write-Step "Generating mock data..."
    $env:PYTHONIOENCODING = "utf-8"
    python "$ROOT_DIR\backend\mock_data\generate_claims.py"
    python "$ROOT_DIR\backend\mock_data\generate_policies.py"
    python "$ROOT_DIR\backend\mock_data\generate_fhir_data.py"
    python "$ROOT_DIR\backend\mock_data\generate_fraud_training.py"
    Write-Host "Mock data generated successfully!" -ForegroundColor Green
}

function Start-Backend {
    Write-Step "Starting ClaimPilot backend (FastAPI)..."
    $env:PYTHONIOENCODING = "utf-8"
    Push-Location $ROOT_DIR\backend
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    Pop-Location
}

function Start-Frontend {
    Write-Step "Starting ClaimPilot frontend (Next.js)..."
    Push-Location $ROOT_DIR\frontend
    npm install
    npm run dev
    Pop-Location
}

function Run-Tests {
    Write-Step "Running tests..."
    $env:PYTHONIOENCODING = "utf-8"
    Push-Location $ROOT_DIR\backend
    python -m pytest tests/ -v
    Pop-Location
}

switch ($Target) {
    "mock-data" { Generate-MockData }
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "test" { Run-Tests }
    "all" {
        Generate-MockData
        Write-Host "`nStart services in separate terminals:"
        Write-Host "  .\scripts\run.ps1 backend" -ForegroundColor Yellow
        Write-Host "  .\scripts\run.ps1 frontend" -ForegroundColor Yellow
    }
}
