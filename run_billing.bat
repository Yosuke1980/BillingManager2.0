@echo off
chcp 65001 >nul
rem BillingManager簡易起動スクリプト (Windows用)

cd /d %~dp0

rem Python環境の設定
set PYTHONDONTWRITEBYTECODE=1
set PYTHONWARNINGS=ignore
set PIP_DISABLE_PIP_VERSION_CHECK=1

rem Pythonコマンドの確認
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

rem アプリケーションを起動（GUIモード）
if exist "%PYTHON_CMD%w.exe" (
    %PYTHON_CMD%w app.pyw
) else (
    %PYTHON_CMD% app.pyw
)

rem エラーがあれば待機
if %errorlevel% neq 0 (
    echo アプリケーションの起動に失敗しました
    pause
)