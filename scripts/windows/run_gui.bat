@echo off
REM Launch Streamlit GUI for Louisiana Census Data Explorer

setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."

echo.
echo ========================================
echo Louisiana Census Data Explorer
echo ========================================
echo.

REM Check if Ollama is running
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Ollama does not appear to be running!
    echo Please start Ollama first:
    echo   ollama serve
    echo.
    echo Or in another terminal:
    echo   ollama run phi3:mini
    echo.
    pause
)

REM Check if in virtual environment
if not exist ".venv\Scripts\streamlit.exe" (
    echo.
    echo ERROR: Streamlit not found in virtual environment!
    echo.
    echo Please install dependencies:
    echo   scripts\windows\setup_uv.bat
    echo   OR
    echo   uv add -r requirements.txt
    echo.
    pause
    popd
    exit /b 1
)

echo.
echo Starting Streamlit GUI...
echo Access the app at: http://localhost:8501
echo Press Ctrl+C to stop
echo.

REM Launch Streamlit
.venv\Scripts\streamlit.exe run gui\app.py

pause
popd
