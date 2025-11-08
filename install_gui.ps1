# Install GUI dependencies for Louisiana Census Agent

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing GUI Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Installing Streamlit, Folium, and streamlit-folium..." -ForegroundColor Yellow
Write-Host ""

# First, try to reinstall if there's a partial installation
Write-Host "Cleaning any partial installations..." -ForegroundColor Gray
uv pip uninstall -q pydeck altair 2>$null

# Install with system copy (no hardlinks)
Write-Host "Installing packages (this may take 30-60 seconds)..." -ForegroundColor Gray
$env:UV_LINK_MODE = "copy"
$env:SYSTEMROOT = $env:SystemRoot

# Install one at a time to avoid conflicts
uv pip install --no-cache folium
uv pip install --no-cache streamlit-folium  
uv pip install --no-cache streamlit

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to install GUI dependencies" -ForegroundColor Red
    Write-Host ""
    Write-Host "This might be due to OneDrive file locking." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Workaround:" -ForegroundColor Yellow
    Write-Host "1. Close OneDrive temporarily" -ForegroundColor White
    Write-Host "2. Run: uv pip install --no-cache streamlit folium streamlit-folium" -ForegroundColor White
    Write-Host "3. Restart OneDrive" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GUI Dependencies Installed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installed packages:" -ForegroundColor Yellow
Write-Host "  - streamlit (web framework)" -ForegroundColor White
Write-Host "  - folium (interactive maps)" -ForegroundColor White
Write-Host "  - streamlit-folium (map integration)" -ForegroundColor White
Write-Host ""
Write-Host "You can now run the GUI:" -ForegroundColor Yellow
Write-Host "  .\run_gui.ps1" -ForegroundColor Cyan
Write-Host "  OR" -ForegroundColor Yellow
Write-Host "  streamlit run gui\app.py" -ForegroundColor Cyan
Write-Host ""
