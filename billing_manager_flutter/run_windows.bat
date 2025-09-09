@echo off
chcp 65001 > nul
title ラジオ局支払い・費用管理システム (Flutter版)

echo ==================================================
echo   ラジオ局支払い・費用管理システム (Flutter版)
echo ==================================================
echo.

REM バッチファイルのディレクトリに移動
cd /d "%~dp0"

REM Flutter環境のチェック
echo 🔍 Flutter環境をチェック中...
flutter --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flutterが見つかりません。
    echo.
    echo Flutterをインストールするには：
    echo 1. https://flutter.dev/docs/get-started/install/windows にアクセス
    echo 2. Flutter SDKをダウンロードして展開
    echo 3. システム環境変数のPATHに追加
    echo 4. コマンドプロンプトを再起動
    echo.
    pause
    exit /b 1
)
echo ✅ Flutter環境を確認しました

REM pubspec.yamlの存在確認
if not exist "pubspec.yaml" (
    echo ❌ pubspec.yamlが見つかりません。
    echo 正しいプロジェクトディレクトリで実行してください。
    pause
    exit /b 1
)

REM 依存関係のインストール
echo.
echo 📦 依存関係をチェック中...
echo 📥 パッケージをインストール中...
flutter pub get
if %errorlevel% neq 0 (
    echo ❌ 依存関係のインストールに失敗しました
    echo.
    echo 以下を確認してください：
    echo - インターネット接続が正常
    echo - Flutter環境が正しく設定されている
    echo - プロジェクトディレクトリが正しい
    pause
    exit /b 1
)
echo ✅ 依存関係のインストール完了

REM Windowsデスクトップサポートの確認
echo.
echo 🔧 Windows デスクトップサポートを確認中...
flutter config --enable-windows-desktop > nul 2>&1

REM アプリケーション起動
echo.
echo 🚀 アプリケーションを起動中...
echo    ※初回起動は時間がかかる場合があります
echo    ※起動後はこのウィンドウを閉じないでください
echo.

REM Windowsアプリとして起動
flutter run -d windows

REM 終了処理
if %errorlevel% neq 0 (
    echo.
    echo ❌ アプリケーションの起動に失敗しました
    echo.
    echo 問題が解決しない場合は、以下のコマンドを実行してください：
    echo flutter doctor
    echo.
    echo または以下を確認してください：
    echo - Visual Studio または Visual Studio Build Tools がインストールされている
    echo - Windows 10 SDK がインストールされている
    echo - Flutter のWindows デスクトップサポートが有効
    pause
    exit /b 1
)

echo.
echo ✅ アプリケーションが終了しました
echo またのご利用をお待ちしています！
echo.
pause