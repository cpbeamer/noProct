@echo off
echo ========================================
echo Question Assistant Installer for Python 3.12
echo ========================================
echo.

:: Check Python version
python --version 2>&1 | findstr /C:"3.12" >nul
if errorlevel 1 (
    echo Warning: Python 3.12 not detected. This installer is optimized for Python 3.12
    echo.
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip and setuptools
echo.
echo Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel

:: Install dependencies one by one for better error handling
echo.
echo Installing core dependencies...

:: Core packages
python -m pip install pywin32==306
python -m pip install mss==9.0.1
python -m pip install Pillow==10.1.0
python -m pip install numpy==1.26.2
python -m pip install opencv-python==4.8.1.78
python -m pip install pytesseract==0.3.10
python -m pip install pyautogui==0.9.54
python -m pip install pynput==1.7.6

echo.
echo Installing AI and web packages...
python -m pip install anthropic==0.18.0
python -m pip install requests==2.31.0
python -m pip install beautifulsoup4==4.12.2

echo.
echo Installing UI packages...
python -m pip install customtkinter==5.2.1
python -m pip install pystray==0.19.5
python -m pip install plyer==2.1

echo.
echo Installing monitoring packages...
python -m pip install psutil==5.9.6
python -m pip install cachetools==5.3.2

echo.
echo Installing security packages...
python -m pip install cryptography==41.0.5
python -m pip install keyring==24.3.0

echo.
echo Installing additional packages...
python -m pip install packaging==23.2
python -m pip install babel==2.13.1
python -m pip install pytz==2023.3

:: Optional packages (continue on error)
echo.
echo Installing optional packages...
python -m pip install matplotlib==3.8.2 2>nul
python -m pip install scipy==1.11.4 2>nul
python -m pip install scikit-learn==1.3.2 2>nul

:: Create necessary directories
echo.
echo Creating project directories...
if not exist config mkdir config
if not exist logs mkdir logs
if not exist templates mkdir templates
if not exist templates\buttons mkdir templates\buttons
if not exist templates\patterns mkdir templates\patterns

:: Check for Tesseract
echo.
echo Checking for Tesseract OCR...
where tesseract >nul 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Tesseract OCR not found!
    echo Please download and install from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
) else (
    echo Tesseract OCR found.
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Make sure virtual environment is activated
echo   2. Run: python main.py
echo.
echo To test the installation:
echo   Run: python test_installation.py
echo.
pause