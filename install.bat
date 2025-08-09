@echo off
echo Installing Question Assistant dependencies...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Download Tesseract if not installed
echo.
echo Checking for Tesseract OCR...
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Tesseract OCR not found!
    echo Please download and install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Make sure to add it to PATH during installation
    pause
)

echo.
echo Installation complete!
echo.
echo To run the application:
echo 1. Run: venv\Scripts\activate.bat
echo 2. Run: python main.py
echo.
pause