@echo off
REM build.bat — Build QRX-Desktop as a Windows .exe using PyInstaller

set APP_NAME=QRX-Desktop
set ENTRY=main.py
set ICON=assets\icon.png

echo === Building %APP_NAME% for Windows ===

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Install dependencies
pip install -r requirements.txt

REM Run PyInstaller (with or without icon)
if exist "%ICON%" (
    pyinstaller --onefile --windowed --name "%APP_NAME%" --icon "%ICON%" "%ENTRY%"
) else (
    pyinstaller --onefile --windowed --name "%APP_NAME%" "%ENTRY%"
)

echo.
echo Build complete! Find your app in: dist\%APP_NAME%.exe
pause
