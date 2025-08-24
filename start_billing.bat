@echo off
chcp 932 >nul
cd /d %~dp0

rem Python環境の設定とpipの表示抑制
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

rem 依存関係の確認
echo 依存関係を確認中...
%PYTHON_CMD% -c "import PyQt5, watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo 必要なライブラリがインストールされていません
    echo 以下のコマンドでインストールしてください:
    echo pip install --quiet -r requirements.txt
    pause
    exit /b 1
)
echo 依存関係OK

rem バックグラウンドでアプリを起動（GUI用pythonwを使用）
if exist "%PYTHON_CMD%w.exe" (
    start "" /min %PYTHON_CMD%w app.pyw
) else (
    start "" /min %PYTHON_CMD% app.pyw
)

echo BillingManagerを起動しました
timeout /t 2 /nobreak >nul