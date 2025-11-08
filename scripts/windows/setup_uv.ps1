# Louisiana Census Agent - Setup with UV
# This script rebuilds your environment with only necessary packages

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot

Write-Host "" 
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Louisiana Census Agent - UV Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if uv is installed
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "ERROR: uv is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install uv with:" -ForegroundColor Yellow
    Write-Host "  pip install uv" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor Yellow
    Write-Host "  powershell -c ""irm https://astral.sh/uv/install.ps1 | iex""" -ForegroundColor White
    Write-Host ""
    Pop-Location
    exit 1
}

Write-Host "OK - uv is installed" -ForegroundColor Green
Write-Host ""

# Option 1: Clean rebuild
Write-Host "Choose setup option:" -ForegroundColor Yellow
Write-Host "  1. Clean rebuild (removes .venv and starts fresh)" -ForegroundColor White
Write-Host "  2. Sync dependencies (updates existing .venv)" -ForegroundColor White
Write-Host "  3. Cancel" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1, 2, or 3)"

if ($choice -eq "3") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    Pop-Location
    exit 0
}

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Removing old .venv..." -ForegroundColor Yellow
    if (Test-Path .venv) {
        Remove-Item -Recurse -Force .venv
        Write-Host "OK - Old .venv removed" -ForegroundColor Green
    } else {
        Write-Host "OK - No .venv to remove" -ForegroundColor Green
    }
    Write-Host ""
    
    Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
    uv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create venv" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "OK - Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

Write-Host "Syncing dependencies from requirements.txt..." -ForegroundColor Yellow
# Use copy mode for OneDrive compatibility
$env:UV_LINK_MODE = "copy"
uv pip sync requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to sync dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "OK - Dependencies synced" -ForegroundColor Green
Write-Host ""

# Show installed packages
Write-Host "Installed packages:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
uv pip list
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the setup:" -ForegroundColor White
Write-Host "     python main.py --help" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Run tests:" -ForegroundColor White
Write-Host "     python tests\test_intent.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Start querying:" -ForegroundColor White
Write-Host "     python main.py" -ForegroundColor Gray
Write-Host ""
pause
Pop-Location
