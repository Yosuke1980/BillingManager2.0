@echo off
chcp 65001 >nul
echo Flutter Debug Information (Windows)
echo ========================================
echo.

echo [1/5] Flutter Version:
flutter --version
echo.

echo [2/5] Flutter Doctor:
flutter doctor -v
echo.

echo [3/5] Available Devices:
flutter devices
echo.

echo [4/5] Project Dependencies Check:
flutter pub deps
echo.

echo [5/5] Windows Desktop Support Check:
flutter config --enable-windows-desktop
echo.

echo Debug information complete.
echo If there are issues above, please share the output.
echo.
pause