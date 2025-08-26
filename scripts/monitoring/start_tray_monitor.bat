@echo off
chcp 65001 >nul
rem ファイル監視トレイアプリ起動スクリプト (Windows用)

setlocal
set SCRIPT_DIR=%~dp0
set TRAY_SCRIPT=%SCRIPT_DIR%tray_monitor.py

rem Pythonコマンドの確認(python3 -> pythonの順に実行)
set PYTHON_CMD=python
where %PYTHON_CMD% >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=python3
    where %PYTHON_CMD% >nul 2>&1
    if %errorlevel% neq 0 (
        echo エラー: PythonまたはPython3がインストールされていません
        pause
        exit /b 1
    )
)

rem スクリプトファイルの存在確認
if not exist "%TRAY_SCRIPT%" (
    echo エラー: tray_monitor.pyが見つかりません
    echo パス: %TRAY_SCRIPT%
    pause
    exit /b 1
)

rem 依存関係の確認
set PYTHONDONTWRITEBYTECODE=1
set PYTHONWARNINGS=ignore
set PIP_DISABLE_PIP_VERSION_CHECK=1
echo 依存関係を確認中...
%PYTHON_CMD% -c "import PyQt5, watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo 必要なライブラリがインストールされていません
    echo 以下のコマンドでインストールしてください:
    echo pip install --quiet -r requirements.txt
    echo または個別にインストール:
    echo pip install --quiet PyQt5 watchdog psutil
    pause
    exit /b 1
)
echo 依存関係OK

rem 引数の処理
if "%~1"=="" goto :start_tray
if /i "%~1"=="start" goto :start_tray
if /i "%~1"=="stop" goto :stop_tray
if /i "%~1"=="status" goto :check_status
goto :show_usage

:show_usage
echo 使用方法:
echo   %0          - トレイアプリを起動
echo   %0 start    - トレイアプリを起動  
echo   %0 stop     - トレイアプリを停止
echo   %0 status   - 実行状態を確認
pause
goto :eof

:start_tray
echo BillingManager ファイル監視トレイアプリを起動します...

rem 既に起動済みかチェック
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "tray_monitor.py" >nul
if %errorlevel% equ 0 (
    echo トレイアプリは既に起動済みです
    pause
    goto :eof
)

rem バックグラウンドで起動(GUI用pythonwを使用)
if exist "%PYTHON_CMD%w.exe" (
    set PYTHON_GUI_CMD=%PYTHON_CMD%w
) else (
    set PYTHON_GUI_CMD=%PYTHON_CMD%
)
start "" /min %PYTHON_GUI_CMD% "%TRAY_SCRIPT%"

timeout /t 2 /nobreak >nul

echo トレイアプリを起動しました
echo システムトレイのアイコンを確認してください
pause
goto :eof

:stop_tray
echo トレイアプリを停止します...

rem プロセスを検索して停止
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "tray_monitor.py"') do (
    taskkill /PID %%i /F >nul 2>&1
)

echo トレイアプリを停止しました
pause
goto :eof

:check_status
echo トレイアプリの実行状態を確認中...

tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "tray_monitor.py" >nul
if %errorlevel% equ 0 (
    echo トレイアプリは実行中です
) else (
    echo トレイアプリは停止中です
)

pause
goto :eof