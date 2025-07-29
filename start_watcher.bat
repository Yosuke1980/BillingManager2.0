@echo off
rem CSVファイル監視スクリプトの起動/停止用スクリプト (Windows用)

setlocal
set SCRIPT_DIR=%~dp0
set WATCHER_SCRIPT=%SCRIPT_DIR%file_watcher.py
set PYTHON_CMD=python

rem Pythonの存在確認
where %PYTHON_CMD% >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)

rem 引数の処理
if "%~1"=="" goto :show_usage
if /i "%~1"=="start" goto :start_watcher
if /i "%~1"=="stop" goto :stop_watcher
if /i "%~1"=="status" goto :check_status
if /i "%~1"=="restart" goto :restart_watcher
goto :show_usage

:check_dependencies
echo 依存関係を確認中...
%PYTHON_CMD% -c "import watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo 必要なライブラリがインストールされていません
    echo 以下のコマンドでインストールしてください:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)
echo 依存関係OK
goto :eof

:show_usage
echo 使用方法:
echo   %0 start   - ファイル監視を開始
echo   %0 stop    - ファイル監視を停止
echo   %0 status  - ファイル監視の状態を確認
echo   %0 restart - ファイル監視を再起動
pause
goto :eof

:start_watcher
echo CSVファイル監視を開始します...
call :check_dependencies
if %errorlevel% neq 0 exit /b %errorlevel%

rem バックグラウンドで実行
start "" /min %PYTHON_CMD% "%WATCHER_SCRIPT%"

timeout /t 2 /nobreak >nul

rem 起動確認
%PYTHON_CMD% "%WATCHER_SCRIPT%" --status
pause
goto :eof

:stop_watcher
echo CSVファイル監視を停止します...
%PYTHON_CMD% "%WATCHER_SCRIPT%" --stop
pause
goto :eof

:check_status
%PYTHON_CMD% "%WATCHER_SCRIPT%" --status
pause
goto :eof

:restart_watcher
echo CSVファイル監視を再起動します...
call :stop_watcher
timeout /t 3 /nobreak >nul
call :start_watcher
goto :eof