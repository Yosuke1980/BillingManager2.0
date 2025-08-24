@echo off
chcp 932 >nul
rem CSV�t�@�C���Ď��X�N���v�g�̋N��/��~�p�X�N���v�g (Windows�p)

setlocal
set SCRIPT_DIR=%~dp0
set WATCHER_SCRIPT=%SCRIPT_DIR%file_watcher.py

rem Python�R�}���h�̊m�F�ipython3 -> python �̏��Ɏ��s�j
set PYTHON_CMD=python
where %PYTHON_CMD% >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=python3
    where %PYTHON_CMD% >nul 2>&1
    if %errorlevel% neq 0 (
        echo �G���[: Python�܂���Python3���C���X�g�[������Ă��܂���
        pause
        exit /b 1
    )
)

rem �X�N���v�g�t�@�C���̑��݊m�F
if not exist "%WATCHER_SCRIPT%" (
    echo �G���[: file_watcher.py��������܂���
    echo �p�X: %WATCHER_SCRIPT%
    pause
    exit /b 1
)

rem �����̏���
if "%~1"=="" goto :show_usage
if /i "%~1"=="start" goto :start_watcher
if /i "%~1"=="stop" goto :stop_watcher
if /i "%~1"=="status" goto :check_status
if /i "%~1"=="restart" goto :restart_watcher
goto :show_usage

:check_dependencies
echo �ˑ��֌W���m�F��...
set PYTHONDONTWRITEBYTECODE=1
set PYTHONWARNINGS=ignore
set PIP_DISABLE_PIP_VERSION_CHECK=1
%PYTHON_CMD% -c "import watchdog, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo �K�v�ȃ��C�u�������C���X�g�[������Ă��܂���
    echo �ȉ��̃R�}���h�ŃC���X�g�[�����Ă�������:
    echo pip install --quiet -r requirements.txt
    echo �܂��͌ʂɃC���X�g�[��:
    echo pip install --quiet watchdog psutil
    pause
    exit /b 1
)
echo �ˑ��֌WOK
goto :eof

:show_usage
echo �g�p���@:
echo   %0 start   - �t�@�C���Ď����J�n
echo   %0 stop    - �t�@�C���Ď����~
echo   %0 status  - �t�@�C���Ď��̏�Ԃ��m�F
echo   %0 restart - �t�@�C���Ď����ċN��
pause
goto :eof

:start_watcher
echo CSV�t�@�C���Ď����J�n���܂�...
call :check_dependencies
if %errorlevel% neq 0 exit /b %errorlevel%

rem �o�b�N�O���E���h�Ŏ��s
start "" /min %PYTHON_CMD% "%WATCHER_SCRIPT%"

timeout /t 2 /nobreak >nul

rem �N���m�F
%PYTHON_CMD% "%WATCHER_SCRIPT%" --status
pause
goto :eof

:stop_watcher
echo CSV�t�@�C���Ď����~���܂�...
%PYTHON_CMD% "%WATCHER_SCRIPT%" --stop
pause
goto :eof

:check_status
%PYTHON_CMD% "%WATCHER_SCRIPT%" --status
pause
goto :eof

:restart_watcher
echo CSV�t�@�C���Ď����ċN�����܂�...
call :stop_watcher
timeout /t 3 /nobreak >nul
call :start_watcher
goto :eof