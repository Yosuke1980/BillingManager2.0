@echo off
chcp 65001 >nul
echo Radio Station Payment and Expense Management System Flutter (Windows)
echo.
echo Starting Flutter application...
echo.

REM Enhanced Flutter path detection
set FLUTTER_PATH=
REM Check common installation paths
if exist "C:\flutter\bin\flutter.exe" (
    set FLUTTER_PATH=C:\flutter\bin\flutter.exe
) else if exist "C:\tools\flutter\bin\flutter.exe" (
    set FLUTTER_PATH=C:\tools\flutter\bin\flutter.exe
) else if exist "%USERPROFILE%\flutter\bin\flutter.exe" (
    set FLUTTER_PATH=%USERPROFILE%\flutter\bin\flutter.exe
) else if exist "%LOCALAPPDATA%\flutter\bin\flutter.exe" (
    set FLUTTER_PATH=%LOCALAPPDATA%\flutter\bin\flutter.exe
) else if exist "C:\src\flutter\bin\flutter.exe" (
    set FLUTTER_PATH=C:\src\flutter\bin\flutter.exe
) else (
    REM Try to find flutter in PATH
    for %%i in (flutter.exe) do (
        if not "%%~$PATH:i"=="" (
            set FLUTTER_PATH=%%~$PATH:i
        )
    )
)

REM Final check
if "%FLUTTER_PATH%"=="" (
    echo Error: Flutter not found.
    echo Please install Flutter and add it to your PATH.
    echo Common installation paths:
    echo - C:\flutter\bin
    echo - C:\tools\flutter\bin
    echo - %USERPROFILE%\flutter\bin
    pause
    exit /b 1
)

echo Found Flutter at: %FLUTTER_PATH%
echo.

REM Enable Windows desktop support
echo Enabling Windows desktop support...
"%FLUTTER_PATH%" config --enable-windows-desktop

REM Install dependencies
echo Installing dependencies...
"%FLUTTER_PATH%" pub get

REM Start the application
echo Starting application...
"%FLUTTER_PATH%" run -d windows

echo.
echo Application has exited.
pause