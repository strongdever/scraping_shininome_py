@echo off
echo ========================================
echo SEO Automation - Installation Script
echo ========================================
echo.

REM Check Python version
python --version
echo.

REM Upgrade pip first
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)
echo.

REM Install greenlet 3.3.0+ first (required for Python 3.13 compatibility)
echo [2/3] Installing greenlet (Python 3.13 compatible version)...
python -m pip install "greenlet>=3.3.0"
if errorlevel 1 (
    echo ERROR: Failed to install greenlet
    pause
    exit /b 1
)
echo.

REM Install all requirements
echo [3/3] Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ========================================
    echo INSTALLATION FAILED
    echo ========================================
    echo.
    echo If you're using Python 3.13, you may need to:
    echo 1. Use Python 3.11 or 3.12 instead (recommended)
    echo 2. Install Visual Studio Build Tools for C++ compilation
    echo.
    echo See README.md for more troubleshooting information.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installing Playwright browsers...
echo ========================================
python -m playwright install chromium
if errorlevel 1 (
    echo Warning: Failed to install Playwright browsers
    echo You can try manually: playwright install chromium
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo You can now run the automation with:
echo   python seo_automation.py
echo   or
echo   run.bat
echo.
pause

