@echo off
title Question Assistant Pro
color 0B

:: Change to script directory
cd /d "%~dp0"

echo ============================================================
echo          QUESTION ASSISTANT PRO - LAUNCHER
echo ============================================================
echo.

:: Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found. Installing...
    echo.
    
    :: Check Python version and use appropriate installer
    python --version 2>&1 | findstr /C:"3.12" >nul
    if errorlevel 1 (
        call install.bat
    ) else (
        echo Detected Python 3.12, using compatible installer...
        call install_py312.bat
    )
    
    if errorlevel 1 (
        echo.
        echo Installation failed! Please run install_py312.bat manually.
        pause
        exit /b 1
    )
    echo.
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if main packages are installed
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo.
    echo Required packages not found. Installing minimal requirements...
    pip install -r requirements_minimal.txt
    if errorlevel 1 (
        echo.
        echo Failed to install requirements!
        echo Please run: pip install -r requirements_minimal.txt
        pause
        exit /b 1
    )
)

:: Launch the application
echo.
echo Launching Question Assistant Pro...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Application crashed or failed to start!
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure all dependencies are installed:
    echo    pip install -r requirements_minimal.txt
    echo.
    echo 2. Check if Tesseract OCR is installed:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 3. Try running directly:
    echo    python main.py
    echo.
    echo 4. Check the logs folder for error details
    echo ============================================================
    pause
)

exit /b 0