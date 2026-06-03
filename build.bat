@echo off
REM build.bat — Build QRX-Desktop as a Windows .exe using PyInstaller
REM Usage: double-click or run from Command Prompt / PowerShell

set APP_NAME=QRX-Desktop
set ENTRY=main.py
set ICON=assets\icon.ico

echo.
echo ============================================
echo   Building %APP_NAME% for Windows
echo ============================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Install dependencies
echo [1/2] Installing dependencies ...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Aborting.
    pause
    exit /b 1
)

REM Run PyInstaller
echo [2/2] Running PyInstaller ...
if exist "%ICON%" (
    pyinstaller --noconfirm --onefile --noconsole --name "%APP_NAME%" --icon "%ICON%" "%ENTRY%"
) else (
    pyinstaller --noconfirm --onefile --noconsole --name "%APP_NAME%" "%ENTRY%"
)

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\%APP_NAME%.exe
echo ============================================
pause
