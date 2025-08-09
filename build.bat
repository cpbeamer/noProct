@echo off
echo Building Question Assistant executable...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Create directories if they don't exist
if not exist templates mkdir templates
if not exist logs mkdir logs
if not exist config mkdir config

REM Run PyInstaller
echo Running PyInstaller...
pyinstaller build.spec --clean

echo.
echo Build complete!
echo Executable is located in: dist\QuestionAssistant.exe
echo.
pause