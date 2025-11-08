# Louisiana Census Data Explorer - GUI
# Launch Streamlit GUI

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot

try {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Louisiana Census Data Explorer" -ForegroundColor Cyan  
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Note: Make sure Ollama is running (ollama serve)" -ForegroundColor Yellow
    Write-Host ""

    $streamlitPath = Join-Path $repoRoot ".venv\Scripts\streamlit.exe"
    if (-not (Test-Path $streamlitPath)) {
        Write-Host ""
        Write-Host "ERROR: Streamlit not found in virtual environment!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install dependencies:" -ForegroundColor Yellow
        Write-Host "  scripts\windows\setup_uv.ps1" -ForegroundColor White
        Write-Host "  OR" -ForegroundColor Yellow
        Write-Host "  uv add -r requirements.txt" -ForegroundColor White
        Write-Host ""
        pause
        exit 1
    }

    Write-Host ""
    Write-Host "Starting Streamlit GUI..." -ForegroundColor Green
    Write-Host "Access the app at: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""

    & $streamlitPath run gui\app.py
}
finally {
    Pop-Location
}
