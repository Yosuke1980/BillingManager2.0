@echo off
chcp 65001 >nul
cd /d %~dp0

rem Python���ϐ��ݒ�ipip�x������j
set PYTHONDONTWRITEBYTECODE=1
set PYTHONWARNINGS=ignore
set PIP_DISABLE_PIP_VERSION_CHECK=1

rem Python�R�}���h�̊m�F
set PYTHON_CMD=python3
where %PYTHON_CMD% >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=python
    where %PYTHON_CMD% >nul 2>&1
    if %errorlevel% neq 0 (
        echo �G���[: Python�܂���python3���C���X�g�[������Ă��܂���
        pause
        exit /b 1
    )
)

rem �ˑ��֌W�̊m�F
echo �ˑ��֌W���m�F��...
%PYTHON_CMD% -c "import PyQt5, watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo �K�v�ȃ��C�u�������C���X�g�[������Ă��܂���
    echo �ȉ��̃R�}���h�ŃC���X�g�[�����Ă�������:
    echo pip install --quiet -r requirements.txt
    pause
    exit /b 1
)
echo �ˑ��֌WOK

rem �o�b�N�O���E���h�ŃA�v�����N���iGUI�ppythonw���g�p�j
if exist "%PYTHON_CMD%w.exe" (
    start "" /min %PYTHON_CMD%w app.pyw
) else (
    start "" /min %PYTHON_CMD% app.pyw
)

echo BillingManager���N�����܂���
timeout /t 2 /nobreak >nul