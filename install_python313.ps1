# 自動下載並安裝 Python 3.13.11

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Python 3.13.11 Installation" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$pythonUrl = "https://www.python.org/ftp/python/3.13.11/python-3.13.11-amd64.exe"
$installerPath = "$env:TEMP\python-3.13.11-amd64.exe"

Write-Host "Downloading Python 3.13.11..." -ForegroundColor Cyan
Write-Host "URL: $pythonUrl" -ForegroundColor Gray
Write-Host ""

try {
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Download completed successfully!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Starting installer..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "IMPORTANT: During installation, please:" -ForegroundColor Yellow
    Write-Host "  1. Check 'Add Python 3.13 to PATH'" -ForegroundColor Yellow
    Write-Host "  2. Check 'Install for all users' (recommended)" -ForegroundColor Yellow
    Write-Host "  3. Select 'Customize installation' and check 'py launcher'" -ForegroundColor Yellow
    Write-Host ""
    
    Start-Process $installerPath -Wait
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Installation process completed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Close this window and open a NEW PowerShell window" -ForegroundColor White
    Write-Host "2. Verify installation: py -3.13 --version" -ForegroundColor White
    Write-Host "3. Follow the instructions in SETUP_PYTHON_313.md" -ForegroundColor White
    Write-Host ""
    
}
catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host $pythonUrl -ForegroundColor White
    exit 1
}
