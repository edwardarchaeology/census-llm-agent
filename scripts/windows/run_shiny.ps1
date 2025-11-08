# Run the Shiny GUI
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot

try {
    Write-Host "========================================"
    Write-Host "Louisiana Census Data Explorer - Shiny"
    Write-Host "========================================"
    Write-Host ""

    Write-Host "Starting Shiny app..."
    Write-Host "Access the app at: http://localhost:8000"
    Write-Host "Press Ctrl+C to stop"
    Write-Host ""

    & .\.venv\Scripts\python.exe -m shiny run gui\shiny_app.py --reload --port 8000
}
finally {
    Pop-Location
}
