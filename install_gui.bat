@echo off
REM Install GUI dependencies for Louisiana Census Agent

echo.
echo ========================================
echo Installing GUI Dependencies
echo ========================================
echo.

REM Use uv pip with no-cache to avoid OneDrive issues
echo Installing Streamlit, Folium, and streamlit-folium...
echo.

REM Cleaning any partial installations
echo Cleaning any partial installations...
uv pip uninstall -q pydeck altair 2>nul

REM Install with no cache to avoid OneDrive issues
echo Installing packages (this may take 30-60 seconds)...
set UV_LINK_MODE=copy
set SYSTEMROOT=%SystemRoot%

REM Install one at a time to avoid conflicts
uv pip install --no-cache folium
uv pip install --no-cache streamlit-folium
uv pip install --no-cache streamlit

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install GUI dependencies
    echo.
    echo This might be due to OneDrive file locking.
    echo.
    echo Workaround:
    echo 1. Close OneDrive temporarily
    echo 2. Run: uv pip install --no-cache streamlit folium streamlit-folium
    echo 3. Restart OneDrive
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo GUI Dependencies Installed!
echo ========================================
echo.
echo Installed packages:
echo   - streamlit (web framework)
echo   - folium (interactive maps)
echo   - streamlit-folium (map integration)
echo.
echo You can now run the GUI:
echo   .\run_gui.bat
echo   OR
echo   streamlit run gui\app.py
echo.
pause
