@echo off
REM Windows緊急修復バッチファイル
REM データベース同期問題を強制的に修正

echo ========================================
echo Windows データベース緊急修復
echo ========================================
echo.

cd /d %~dp0

echo [1/5] 現在のディレクトリを確認
cd
echo.

echo [2/5] データベースをバックアップ
if exist order_management.db (
    echo バックアップを作成: order_management.db.emergency_backup
    copy /Y order_management.db order_management.db.emergency_backup
) else (
    echo order_management.db が見つかりません（新規取得します）
)
echo.

echo [3/5] Gitの状態を確認
git status
echo.

echo [4/5] GitHubから強制的に最新版を取得
echo リモートから最新版を取得中...
git fetch origin

echo ローカルをリモートに合わせます...
git reset --hard origin/main
echo.

echo [5/5] データベースファイルを確認
if exist order_management.db (
    echo ✓ order_management.db が存在します
    dir order_management.db
) else (
    echo ✗ order_management.db が見つかりません！
)
echo.

echo ========================================
echo 修復完了
echo ========================================
echo.
echo アプリケーションを起動してください:
echo   python app.py
echo.
pause
