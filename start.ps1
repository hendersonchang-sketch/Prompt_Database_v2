# BananaDB Quick Start Script (PowerShell)

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  BananaDB Starting..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and set GEMINI_API_KEY"
    pause
    exit 1
}

# Check if API key is configured
$envContent = Get-Content ".env" -Raw
if ($envContent -match "your-gemini-api-key-here") {
    Write-Host "WARNING: Gemini API key not configured" -ForegroundColor Red
    Write-Host "Please edit .env file and enter your actual API key"
    pause
    exit 1
}

Write-Host "Environment variables configured" -ForegroundColor Green
Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "Web UI: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app:app --reload --port 8000
