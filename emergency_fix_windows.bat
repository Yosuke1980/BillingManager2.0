@echo off
chcp 65001 > nul
REM Windows Emergency Database Repair Batch File
REM Force fix database synchronization issues

echo ========================================
echo Windows Database Emergency Repair
echo ========================================
echo.

cd /d %~dp0

echo [1/5] Check current directory
cd
echo.

echo [2/5] Backup database
if exist order_management.db (
    echo Creating backup: order_management.db.emergency_backup
    copy /Y order_management.db order_management.db.emergency_backup
) else (
    echo order_management.db not found (will fetch new one)
)
echo.

echo [3/5] Check Git status
git status
echo.

echo [4/5] Force fetch latest version from GitHub
echo Fetching from remote...
git fetch origin

echo Resetting local to match remote...
git reset --hard origin/main
echo.

echo [5/5] Verify database file
if exist order_management.db (
    echo [OK] order_management.db exists
    dir order_management.db
) else (
    echo [ERROR] order_management.db not found!
)
echo.

echo ========================================
echo Repair Complete
echo ========================================
echo.
echo Start the application:
echo   python app.py
echo.
pause
