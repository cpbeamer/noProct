@echo off
title Question Assistant Uninstaller
color 0C

echo.
echo ============================================================
echo            QUESTION ASSISTANT UNINSTALLER
echo ============================================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This uninstaller requires Administrator privileges.
    echo.
    echo Right-click on uninstall.bat and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

:: Change to the script directory
cd /d "%~dp0"

:: Run Python uninstaller if Python is available
python --version >nul 2>&1
if %errorLevel% equ 0 (
    echo Starting uninstallation...
    if exist "%~dp0uninstall.py" (
        python "%~dp0uninstall.py"
    ) else (
        echo Error: uninstall.py not found in %~dp0
        echo Proceeding with manual uninstallation...
    )
    goto :end
)

:: Fallback to manual uninstallation if Python not available
echo Python not found. Performing manual uninstallation...
echo.

:: Stop and remove service
echo Removing Windows service...
net stop QuestionAssistantService >nul 2>&1
sc delete QuestionAssistantService >nul 2>&1

:: Kill running processes
echo Stopping running processes...
taskkill /F /IM main.exe >nul 2>&1
taskkill /F /IM "Question Assistant*" >nul 2>&1
timeout /t 2 /nobreak >nul

:: Remove from startup
echo Removing startup entries...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "QuestionAssistant" /f >nul 2>&1

:: Remove application files
echo Removing application files...
set APP_DIR=%~dp0

:: Remove directories
if exist "%APP_DIR%src" rmdir /s /q "%APP_DIR%src"
if exist "%APP_DIR%config" rmdir /s /q "%APP_DIR%config"
if exist "%APP_DIR%logs" rmdir /s /q "%APP_DIR%logs"
if exist "%APP_DIR%templates" rmdir /s /q "%APP_DIR%templates"
if exist "%APP_DIR%docs" rmdir /s /q "%APP_DIR%docs"
if exist "%APP_DIR%tests" rmdir /s /q "%APP_DIR%tests"
if exist "%APP_DIR%__pycache__" rmdir /s /q "%APP_DIR%__pycache__"
if exist "%APP_DIR%build" rmdir /s /q "%APP_DIR%build"
if exist "%APP_DIR%dist" rmdir /s /q "%APP_DIR%dist"

:: Remove files
if exist "%APP_DIR%main.py" del /f /q "%APP_DIR%main.py"
if exist "%APP_DIR%app.py" del /f /q "%APP_DIR%app.py"
if exist "%APP_DIR%setup.py" del /f /q "%APP_DIR%setup.py"
if exist "%APP_DIR%requirements.txt" del /f /q "%APP_DIR%requirements.txt"
if exist "%APP_DIR%*.spec" del /f /q "%APP_DIR%*.spec"
if exist "%APP_DIR%*.exe" del /f /q "%APP_DIR%*.exe"

:: Remove user data
echo Removing user data...
if exist "%APPDATA%\QuestionAssistant" rmdir /s /q "%APPDATA%\QuestionAssistant"
if exist "%LOCALAPPDATA%\QuestionAssistant" rmdir /s /q "%LOCALAPPDATA%\QuestionAssistant"

:: Remove shortcuts
echo Removing shortcuts...
if exist "%USERPROFILE%\Desktop\Question Assistant.lnk" del /f /q "%USERPROFILE%\Desktop\Question Assistant.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Question Assistant.lnk" del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Question Assistant.lnk"

echo.
echo ============================================================
echo         UNINSTALLATION COMPLETED SUCCESSFULLY
echo ============================================================
echo.
echo Question Assistant has been removed from your system.
echo.
echo NOTE: This uninstall script will remain. You can delete it manually.
echo.

:end
pause
exit /b 0