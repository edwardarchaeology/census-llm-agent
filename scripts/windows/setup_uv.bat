@echo off
REM Simple UV setup for Louisiana Census Agent
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."

echo.
echo ========================================
echo Louisiana Census Agent - UV Setup
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed!
    echo.
    echo Install with: pip install uv
    pause
    popd
    exit /b 1
)

echo OK - uv is installed
echo.

echo Choose setup option:
echo   1. Clean rebuild (removes .venv and starts fresh)
echo   2. Sync dependencies (updates existing .venv)
echo   3. Cancel
echo.

set /p choice="Enter choice (1, 2, or 3): "

if "%choice%"=="3" (
    echo Cancelled.
    popd
    exit /b 0
)

if "%choice%"=="1" (
    echo.
    echo Removing old .venv...
    if exist .venv (
        rmdir /s /q .venv
        echo OK - Old .venv removed
    ) else (
        echo OK - No .venv to remove
    )
    echo.
    
    echo Creating new virtual environment...
    uv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create venv
        pause
        popd
        exit /b 1
    )
    echo OK - Virtual environment created
    echo.
)

echo Syncing dependencies from requirements.txt...
REM Use copy mode for OneDrive compatibility
set UV_LINK_MODE=copy
uv pip sync requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to sync dependencies
    pause
    popd
    exit /b 1
)
echo OK - Dependencies synced
echo.

REM Show installed packages
echo Installed packages:
echo ----------------------------------------
uv pip list
echo ----------------------------------------
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Test the setup: python main.py --help
echo   2. Run tests: python tests\test_intent.py
echo   3. Start querying: python main.py
echo.
pause
popd
exit /b 0
