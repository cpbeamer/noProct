@echo off
echo Starting Question Assistant in System Tray...
echo.
echo The app will run in your system tray (near the clock).
echo You can close this window - the app will continue running.
echo.

:: Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Start in tray mode
python main.py --mode tray

pause