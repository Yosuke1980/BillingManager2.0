@echo off
chcp 65001 >nul
echo Radio Station Payment and Expense Management System Flutter (Windows)
echo.
echo Starting Flutter application...
echo.

REM Check if Flutter is available in PATH
flutter --version >nul 2>&1
if errorlevel 1 (
    echo Error: Flutter not found in PATH.
    echo Please install Flutter and add it to your PATH.
    echo Common installation paths:
    echo - C:\flutter\bin
    echo - C:\tools\flutter\bin
    echo - %USERPROFILE%\flutter\bin
    echo - %USERPROFILE%\dev\flutter\bin
    pause
    exit /b 1
)

echo Found Flutter in PATH
echo.

REM Check Flutter doctor first
echo Checking Flutter setup...
flutter doctor

REM Enable Windows desktop support
echo Enabling Windows desktop support...
flutter config --enable-windows-desktop

REM Clean and get dependencies
echo Cleaning project...
flutter clean

echo Installing dependencies...
flutter pub get

REM Check available devices
echo Checking available devices...
flutter devices

REM Start the application with verbose output
echo Starting application...
flutter run -d windows --verbose

echo.
echo Application has exited.
pause