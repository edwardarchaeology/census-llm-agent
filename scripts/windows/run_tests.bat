@echo off
REM Test Runner for Louisiana Census Agent
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."

echo.
echo ========================================
echo Louisiana Census Agent - Test Runner
echo ========================================
echo.

REM Check if virtual environment exists
if not exist .venv\Scripts\python.exe (
    echo ERROR: Virtual environment not found!
    echo Please run: scripts\windows\setup_uv.bat
    echo OR: uv add -r requirements.txt
    pause
    popd
    exit /b 1
)

REM Use virtual environment Python
set PYTHON=.venv\Scripts\python.exe

echo Using Python: %PYTHON%
echo.

REM Parse command line argument
if "%1"=="" (
    echo Usage: run_tests.bat [test_name]
    echo.
    echo Available tests:
    echo   geography    - Test geography resolution
    echo   multiagent   - Test multi-agent system
    echo   basic        - Test basic functionality
    echo   all          - Run all tests
    echo.
    echo Example: run_tests.bat geography
    pause
    exit /b 0
)

if "%1"=="geography" (
    echo Running geography tests...
    %PYTHON% tests\test_geography.py
    goto :end
)

if "%1"=="multiagent" (
    echo Running multi-agent tests...
    %PYTHON% tests\manual\test_multiagent.py
    goto :end
)

if "%1"=="basic" (
    echo Running basic tests...
    %PYTHON% tests\test_basic.py
    goto :end
)

if "%1"=="all" (
    echo Running all tests...
    echo.
    echo [1/3] Geography tests...
    %PYTHON% tests\test_geography.py
    echo.
    echo [2/3] Basic tests...
    %PYTHON% tests\test_basic.py
    echo.
    echo [3/3] Multi-agent tests...
    %PYTHON% tests\manual\test_multiagent.py
    goto :end
)

echo Unknown test: %1
echo Run without arguments to see available tests.

:end
echo.
echo ========================================
echo Test run complete!
echo ========================================
pause
popd
