# LEX_BY ASOLA Installation Script for Windows
# Downloads and installs LEX security scanner

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LEX_BY ASOLA Security Scanner Installer" -ForegroundColor Green
Write-Host "Built by Asola Junior" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[*] Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[+] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[-] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org" -ForegroundColor Yellow
    exit 1
}

# Check if git is installed
Write-Host "[*] Checking git installation..." -ForegroundColor Cyan
try {
    $gitVersion = git --version 2>&1
    Write-Host "[+] Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[-] Git is not installed" -ForegroundColor Red
    Write-Host "Please install git from https://git-scm.com" -ForegroundColor Yellow
    exit 1
}

# Create installation directory
$installDir = "$env:APPDATA\lex"
if (Test-Path $installDir) {
    Write-Host "[*] LEX directory already exists at $installDir" -ForegroundColor Yellow
    $response = Read-Host "Do you want to reinstall? (y/n)"
    if ($response -ne 'y') {
        exit 0
    }
    Remove-Item -Recurse -Force $installDir
}

# Clone repository
Write-Host "[*] Downloading LEX from GitHub..." -ForegroundColor Cyan
git clone https://github.com/Jumaasola-ops/lex.git $installDir

if (-not $?) {
    Write-Host "[-] Failed to download LEX" -ForegroundColor Red
    exit 1
}

Set-Location $installDir
Write-Host "[+] LEX downloaded successfully" -ForegroundColor Green

# Create virtual environment
Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Cyan
python -m venv venv

if (-not $?) {
    Write-Host "[-] Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate venv and install dependencies
Write-Host "[*] Installing dependencies..." -ForegroundColor Cyan
& ".\venv\Scripts\activate.ps1"
pip install -q -r requirements.txt

if (-not $?) {
    Write-Host "[-] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Installation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "LEX is installed at: $installDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Navigate to: cd $installDir" -ForegroundColor White
Write-Host "2. Activate venv: .\venv\Scripts\activate" -ForegroundColor White
Write-Host "3. Run LEX: python main.py help" -ForegroundColor White
Write-Host ""
Write-Host "For more info, visit: https://github.com/Jumaasola-ops/lex" -ForegroundColor Cyan
