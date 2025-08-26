@echo off
chcp 65001 >nul
rem BillingManagerダブルクリック起動用スクリプト (Windows用)

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

rem バックグラウンドでアプリケーションを起動
if exist "%PYTHON_CMD%w.exe" (
    start /B %PYTHON_CMD%w.exe app.pyw
) else (
    start /B %PYTHON_CMD% app.pyw
)

echo BillingManagerを起動しました