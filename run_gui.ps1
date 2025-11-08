# Louisiana Census Data Explorer - GUI
# Launch Streamlit GUI

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Louisiana Census Data Explorer" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Skip Ollama check - assume it's running
Write-Host "Note: Make sure Ollama is running (ollama serve)" -ForegroundColor Yellow
Write-Host ""

# Check if in virtual environment
if (-not (Test-Path ".venv\Scripts\streamlit.exe")) {
    Write-Host ""
    Write-Host "ERROR: Streamlit not found in virtual environment!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install dependencies:" -ForegroundColor Yellow
    Write-Host "  .\setup_uv.ps1" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "Starting Streamlit GUI..." -ForegroundColor Green
Write-Host "Access the app at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Launch Streamlit
& .venv\Scripts\streamlit.exe run gui\app.py
