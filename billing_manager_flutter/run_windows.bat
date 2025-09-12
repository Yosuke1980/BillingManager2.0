@echo off
echo ラジオ局支払い・費用管理システム Flutter版 (Windows)
echo.
echo Flutterアプリケーションを起動しています...
echo.

REM Flutterのパスを設定
if exist "C:lutterinlutter.exe" (
    set FLUTTER_PATH=C:lutterinlutter.exe
) else if exist "C:	oolslutterinlutter.exe" (
    set FLUTTER_PATH=C:	oolslutterinlutter.exe
) else if exist "%USERPROFILE%lutterinlutter.exe" (
    set FLUTTER_PATH=%USERPROFILE%lutterinlutter.exe
) else (
    echo エラー: Flutterが見つかりません。
    echo Flutterをインストールしてパスを設定してください。
    pause
    exit /b 1
)

REM Windows向けFlutterデスクトップサポートを有効化
%FLUTTER_PATH% config --enable-windows-desktop

REM 依存関係を取得
echo 依存関係をインストール中...
%FLUTTER_PATH% pub get

REM アプリケーションを起動
echo アプリケーションを起動中...
%FLUTTER_PATH% run -d windows

echo.
echo アプリケーションが終了しました。
pause
