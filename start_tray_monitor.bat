@echo off
rem �t�@�C���Ď��g���C�A�v���N���X�N���v�g (Windows�p)

setlocal
set SCRIPT_DIR=%~dp0
set TRAY_SCRIPT=%SCRIPT_DIR%tray_monitor.py
set PYTHON_CMD=python

rem Python�̑��݊m�F
where %PYTHON_CMD% >nul 2>&1
if %errorlevel% neq 0 (
    echo �G���[: Python���C���X�g�[������Ă��܂���
    pause
    exit /b 1
)

rem �ˑ��֌W�̊m�F
echo �ˑ��֌W���m�F��...
%PYTHON_CMD% -c "import PyQt5, watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo �K�v�ȃ��C�u�������C���X�g�[������Ă��܂���
    echo �ȉ��̃R�}���h�ŃC���X�g�[�����Ă�������:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

rem �����̏���
if "%~1"=="" goto :start_tray
if /i "%~1"=="start" goto :start_tray
if /i "%~1"=="stop" goto :stop_tray
if /i "%~1"=="status" goto :check_status
goto :show_usage

:show_usage
echo �g�p���@:
echo   %0          - �g���C�A�v�����N��
echo   %0 start    - �g���C�A�v�����N��
echo   %0 stop     - �g���C�A�v�����~
echo   %0 status   - ���s��Ԃ��m�F
pause
goto :eof

:start_tray
echo BillingManager �t�@�C���Ď��g���C�A�v�����N�����܂�...

rem ���ɋN�������`�F�b�N
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "tray_monitor.py" >nul
if %errorlevel% equ 0 (
    echo �g���C�A�v���͊��ɋN�����ł�
    pause
    goto :eof
)

rem �o�b�N�O���E���h�ŋN��
start "" /min %PYTHON_CMD% "%TRAY_SCRIPT%"

timeout /t 2 /nobreak >nul

echo �g���C�A�v�����N�����܂���
echo �V�X�e���g���C�̃A�C�R�����m�F���Ă�������
pause
goto :eof

:stop_tray
echo �g���C�A�v�����~���܂�...

rem �v���Z�X���������Ē�~
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "tray_monitor.py"') do (
    taskkill /PID %%i /F >nul 2>&1
)

echo �g���C�A�v�����~���܂���
pause
goto :eof

:check_status
echo �g���C�A�v���̎��s��Ԃ��m�F��...

tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "tray_monitor.py" >nul
if %errorlevel% equ 0 (
    echo �g���C�A�v���͎��s���ł�
) else (
    echo �g���C�A�v���͒�~���ł�
)

pause
goto :eof