@echo off
chcp 65001 >nul
echo Radio Station Payment Management - Quick Start
echo.

REM Check if Flutter is available
flutter --version >nul 2>&1
if errorlevel 1 (
    echo Error: Flutter not found in PATH.
    pause
    exit /b 1
)

echo Starting Flutter app directly...
echo Press Ctrl+C to stop if needed.
echo.

REM Enable Windows desktop support (silent)
flutter config --enable-windows-desktop >nul 2>&1

REM Start app with minimal output
flutter run -d windows --release

echo.
echo Application exited.
pause